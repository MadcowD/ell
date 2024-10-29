# A bit of rationale: While it's OOP to put serialization related code in the evaluation and evaliuation run classes it greatly muddies the interface for the purposes of downstream implementaitons therefore much of the bridge between evaluation <-> ell studio should be implemented in this file.

# XXX: we could now move this to the store itself if we so thought. With the exception of ID creaiton.
from typing import cast
from ell.configurator import config

from ell.evaluation.results import _ResultDatapoint
from ell.evaluation.util import needs_store
from ell.lmp._track import serialize_lmp
from ell.store import Store
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
            version_number = (
                max(
                    itertools.chain(
                        map(lambda x: x.version_number, existing_versions), [-1]
                    )
                )
            ) +1 
            if config.autocommit:
                # TODO: Implement
                pass

            # Create SerializedEvaluation
            serialized_evaluation = SerializedEvaluation(
                id=evaluation.id,
                name=evaluation.name,
                dataset_hash=dataset_hash,
                n_evals=evaluation.n_evals or len(evaluation.dataset or []),
                version_number=version_number,
            )

            # Create EvaluationLabelers
            def create_labelers(names, ids, labeler_type):
                return [
                    EvaluationLabeler(
                        name=name,
                        type=labeler_type,
                        evaluation_id=evaluation.id,
                        labeling_lmp_id=h,
                    )
                    for name, h in zip(names, ids)
                ]

            labelers = (
                create_labelers(evaluation.metrics.keys(), metrics_ids, EvaluationLabelerType.METRIC) +
                create_labelers(evaluation.annotations.keys(), annotation_ids, EvaluationLabelerType.ANNOTATION) +
                (create_labelers(["criterion"], criteiron_ids, EvaluationLabelerType.CRITERION) if evaluation.criterion else [])
            )

            # Add labelers to the serialized evaluation
            serialized_evaluation.labelers = labelers
            evaluation.has_serialized = True
            cast(Store, config.store).write_evaluation(serialized_evaluation) 


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

    # Helper function to create labels
    def create_labels(values_dict, labeler_type):
        return [
            EvaluationLabel(
                labeled_datapoint_id=result_datapoint.id,
                labeler_id=EvaluationLabeler.generate_id(
                    evaluation_id=evaluation.id, name=name, type=labeler_type
                ),
                label_invocation_id=values_dict[name][1]
            )
            for name in values_dict
        ]

    # Create labels for metrics and annotations
    result_datapoint.labels.extend(create_labels(
        row_result.metrics, EvaluationLabelerType.METRIC
    ))
    result_datapoint.labels.extend(create_labels(
        row_result.annotations, EvaluationLabelerType.ANNOTATION
    ))

    # Create criterion labels if present
    if row_result.criterion is not None:
        result_datapoint.labels.extend(create_labels(
            {"criterion": row_result.criterion},
            EvaluationLabelerType.CRITERION
        ))
    
    cast(Store, config.store).write_evaluation_run_intermediate(result_datapoint)

@needs_store
def write_evaluation_run_end(evaluation, evaluation_run) -> None:
    # Write summaries using a helper function
    def create_summaries(data_dict, labeler_type):
        return [
            EvaluationRunLabelerSummary.from_labels(
                data=values,
                evaluation_run_id=evaluation_run.id,
                evaluation_labeler_id=EvaluationLabeler.generate_id(
                    evaluation_id=evaluation.id,
                    name=name,
                    type=labeler_type,
                ),
            )
            for name, values in data_dict.items()
        ]

    # Collect summaries for metrics, annotations, and criterion
    summaries = create_summaries(evaluation_run.results.metrics, EvaluationLabelerType.METRIC)
    summaries += create_summaries(evaluation_run.results.annotations, EvaluationLabelerType.ANNOTATION)
    if evaluation_run.results.criterion is not None:
        summaries += create_summaries({"criterion": evaluation_run.results.criterion}, EvaluationLabelerType.CRITERION)

    cast(Store, config.store).write_evaluation_run_end(evaluation_run.id, evaluation_run.success, evaluation_run.end_time, evaluation_run.error, summaries)