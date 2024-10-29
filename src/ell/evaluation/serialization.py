# A bit of rationale: While it's OOP to put serialization related code in the evaluation and evaliuation run classes it greatly muddies the interface for the purposes of downstream implementaitons therefore much of the bridge between evaluation <-> ell studio should be implemented in this file.

# XXX: We've duplicated the SQL model abstractions somewaht pointlessly unfortuantely. If we move to @alex-dixon's API ifciation of the backend then we won't have duplicated data models.
from typing import cast
from ell.configurator import config

from ell.evaluation.results import _ResultDatapoint
from ell.evaluation.util import needs_store
from ell.lmp._track import serialize_lmp
from ell.store import Store
from ell.util._warnings import _autocommit_warning
from ell.util.closure_util import ido
from ell.util.closure_util import hsh
import ell.util.closure
import dill

import itertools

from ell.types.studio.evaluations import (
    EvaluationLabel,
    SerializedEvaluation as SerializedEvaluation,
    EvaluationLabeler,
    EvaluationLabelerType,
    SerializedEvaluationRun,
    EvaluationResultDatapoint,
    EvaluationRunLabelerSummary,
)

@needs_store
def write_evaluation(evaluation) -> None:
    # Create a hash of the dataset and labelers
    
    if not evaluation.has_serialized:
        dataset_hash = hsh(str(dill.dumps(evaluation.dataset) if evaluation.dataset else str(evaluation.n_evals)) + str(evaluation.samples_per_datapoint))
        
        metrics_ids = [ido((f)) for f in evaluation.metrics.values()]
        annotation_ids = [ido((a)) for a in evaluation.annotations.values()]
        criteiron_ids = [ido((evaluation.criterion))] if evaluation.criterion else []
        
        evaluation.id = "evaluation-" + hsh(dataset_hash + "".join(sorted(metrics_ids) + sorted(annotation_ids) + criteiron_ids))
        
        existing_versions = config.store.get_eval_versions_by_name(evaluation.name)
        if any(v.id == evaluation.id for v in existing_versions):
            evaluation.has_serialized = True
        else: 
            # TODO: Merge with other versioning code.
            version_number, latest_version = (
                max(
                    itertools.chain(
                        map(lambda x: (x.version_number, x), existing_versions), 
                        [(-1, None)]
                    ),
                    key=lambda x: x[0]
                )
            )
            version_number += 1
            commit_message = None
            if config.autocommit:
                commit_message = generate_commit_message(evaluation, metrics_ids, annotation_ids, criteiron_ids, latest_version)
                
            # Create SerializedEvaluation
            serialized_evaluation = SerializedEvaluation(
                id=evaluation.id,
                name=evaluation.name,
                dataset_hash=dataset_hash,
                n_evals=evaluation.n_evals or len(evaluation.dataset or []),
                commit_message=commit_message,
                version_number=version_number,
            )


            labelers = [
                EvaluationLabeler(
                    name=labeler.name,
                    type=labeler.type,
                    evaluation_id=evaluation.id,
                    labeling_lmp_id=ido(labeler.label),
                )
                for labeler in evaluation.labels
            ]

            # Add labelers to the serialized evaluation
            serialized_evaluation.labelers = labelers
            evaluation.has_serialized = True
            cast(Store, config.store).write_evaluation(serialized_evaluation) 

def generate_commit_message(evaluation, metrics_ids, annotation_ids, criteiron_ids, latest_version):
    return None
    # XXX
    if not _autocommit_warning():
        from ell.util.differ import write_commit_message_for_diff
                    # Get source code for all metrics, annotations and criterion
                    # In this case we actually dont want to automatically generate a commmit message using gpt-4o we can just detect a cahgne inthe lablers and use that as the primary mechanism.
                    # Get labelers from latest version if it exists
        if latest_version:
            latest_labelers = latest_version.labelers
                        
                        # Group labelers by type
            latest_metrics = {l.name: l.labeling_lmp_id for l in latest_labelers if l.type == EvaluationLabelerType.METRIC}
            latest_annotations = {l.name: l.labeling_lmp_id for l in latest_labelers if l.type == EvaluationLabelerType.ANNOTATION}
            latest_criterion = next((l.labeling_lmp_id for l in latest_labelers if l.type == EvaluationLabelerType.CRITERION), None)

                        # Compare with current labelers
            metrics_changed = {name: id for name, id in zip(evaluation.metrics.keys(), metrics_ids) 
                                        if name not in latest_metrics or latest_metrics[name] != id}
            annotations_changed = {name: id for name, id in zip(evaluation.annotations.keys(), annotation_ids)
                                            if name not in latest_annotations or latest_annotations[name] != id}
            criterion_changed = criteiron_ids[0] if criteiron_ids and (not latest_criterion or latest_criterion != criteiron_ids[0]) else None

            # Generate commit message if there are changes
            if metrics_changed or annotations_changed or criterion_changed:
                changes = []
                summary_parts = []
                if metrics_changed:
                    changes.append(f"Changed metrics: {', '.join(metrics_changed.keys())}")
                    summary_parts.append(f"{len(metrics_changed)} metrics")
                if annotations_changed:
                    changes.append(f"Changed annotations: {', '.join(annotations_changed.keys())}")
                    summary_parts.append(f"{len(annotations_changed)} annotations") 
                if criterion_changed:
                    changes.append("Changed criterion")
                    summary_parts.append("criterion")
                            
                summary = f"Updated {', '.join(summary_parts)}"
                details = " | ".join(changes)
        commit_message = f"{summary}\n\n{details}"
        return commit_message


@needs_store
def write_evaluation_run_start(evaluation, evaluation_run) -> int:
    # Construct SerializedEvaluationRun
    serialized_run = SerializedEvaluationRun(
        evaluation_id=evaluation.id,
        evaluated_lmp_id=ido(evaluation_run.lmp),
        api_params=evaluation_run.api_params,
        start_time=evaluation_run.start_time,
        error=None,
    )
    return cast(Store, config.store).write_evaluation_run(serialized_run)

@needs_store
def write_evaluation_run_intermediate(evaluation, evaluation_run, row_result : _ResultDatapoint) -> None:
    assert evaluation_run.id is not None, "Evaluation run must be started before intermediate results can be written."
    result_datapoint = EvaluationResultDatapoint(
            evaluation_run_id=evaluation_run.id,
            invocation_being_labeled_id=row_result.output[1],
    )

    result_datapoint.labels = [ 
        EvaluationLabel(
            labeled_datapoint_id=result_datapoint.id,
            labeler_id=EvaluationLabeler.generate_id(
                evaluation_id=evaluation.id, name=label.name, type=label.type
            ),
            label_invocation_id=label.label[1]
        )
        for label in row_result.labels
    ]
    
    cast(Store, config.store).write_evaluation_run_intermediate(result_datapoint)

@needs_store
def write_evaluation_run_end(evaluation, evaluation_run) -> None:
    summaries = [
        EvaluationRunLabelerSummary.from_labels(
            data=label.label,
            evaluation_run_id=evaluation_run.id,
            evaluation_labeler_id=EvaluationLabeler.generate_id(
                evaluation_id=evaluation.id,
                name=label.name,
                type=label.type,
            ),
        )
        for label in evaluation_run.results.labels
    ]

    cast(Store, config.store).write_evaluation_run_end(evaluation_run.id, evaluation_run.success, evaluation_run.end_time, evaluation_run.error, summaries)