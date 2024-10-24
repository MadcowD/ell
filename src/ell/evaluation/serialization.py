# A bit of rationale: While it's OOP to put serialization related code in the evaluation and evaliuation run classes it greatly muddies the interface for the purposes of downstream implementaitons therefore much of the bridge between evaluation <-> ell studio should be implemented in this file.

# XXX: we could now move this to the store itself if we so thought. With the exception of ID creaiton.
from ell.configurator import config

from ell.util.closure_util import ido
from ell.util.closure_util import hsh
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

def write_evaluation(evaluation, evaluation_run) -> None:
    # Create a hash of the dataset and labelers
    if not config.store:
        return
    if not evaluation.has_serialized:
        # Todo standardize this.
        dataset_hash = hsh(str(dill.dumps(evaluation.dataset) if evaluation.dataset else str(evaluation.n_evals)) + str(evaluation.samples_per_datapoint))
        metrics_ids = [ido(f) for f in evaluation.metrics.values()]
        annotation_ids = [ido(a) for a in evaluation.annotations.values()]
        criteiron_ids = [ido(evaluation.criterion)] if evaluation.criterion else []
        
        evaluation.id = "evaluation-" + hsh(dataset_hash + "".join(sorted(metrics_ids) + sorted(annotation_ids) + criteiron_ids))

        # get existing versions
        existing_versions = config.store.get_eval_versions_by_name(evaluation.name)
        if any(v.id == evaluation.id for v in existing_versions):
            evaluation.has_serialized = True
        else:
            # TODO: Merge with other versioning code.
            version_number = (
                max(
                    itertools.chain(
                        map(lambda x: x.version_number, existing_versions), [0]
                    )
                )
                + 1
            )

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
            config.store.write_evaluation(serialized_evaluation)

    # Now serialize the evaluation run,
    evaluation_run.write(evaluation_id=evaluation.id)


def write_evaluation_run(evaluation_run, evaluation_id: str):
    if not config.store:
        return

    # Construct SerializedEvaluationRun
    serialized_run = SerializedEvaluationRun(
        evaluation_id=evaluation_id,
        evaluated_lmp_id=ido(evaluation_run.lmp),
        api_params=evaluation_run.api_params,
        start_time=evaluation_run.start_time,
        end_time=evaluation_run.end_time,
        success=True,
        error=None,
    )
    invocation_ids = evaluation_run.results.invocation_ids

    # Create EvaluationResultDatapoints
    result_datapoints = []
    for i, output in enumerate(evaluation_run.results.outputs):
        result_datapoint = EvaluationResultDatapoint(
            invocation_being_labeled_id=ido(evaluation_run.lmp),
            evaluation_run_id=serialized_run.id,
            invocation_ids=invocation_ids.outputs[i],
        )

        # Helper function to create labels
        def create_labels(values_dict, labeler_type, invocation_ids_dict):
            return [
                EvaluationLabel(
                    labeled_datapoint_id=result_datapoint.id,
                    labeler_id=EvaluationLabeler.generate_id(
                        evaluation_id=evaluation_id, name=name, type=labeler_type
                    ),
                    label_invocation_id=invocation_ids_dict[name][i],
                )
                for name in values_dict
            ]

        # Create labels for metrics and annotations
        result_datapoint.labels.extend(create_labels(
            evaluation_run.results.metrics, EvaluationLabelerType.METRIC, invocation_ids.metrics
        ))
        result_datapoint.labels.extend(create_labels(
            evaluation_run.results.annotations, EvaluationLabelerType.ANNOTATION, invocation_ids.annotations
        ))

        # Create criterion labels if present
        if evaluation_run.results.criterion is not None:
            result_datapoint.labels.extend(create_labels(
                {"criterion": evaluation_run.results.criterion},
                EvaluationLabelerType.CRITERION,
                {"criterion": invocation_ids.criterion}
            ))

        result_datapoints.append(result_datapoint)

    serialized_run.results = result_datapoints

    # Write summaries using a helper function
    def create_summaries(data_dict, labeler_type):
        return [
            EvaluationRunLabelerSummary.from_labels(
                data=values,
                evaluation_run_id=id,
                evaluation_labeler_id=EvaluationLabeler.generate_id(
                    evaluation_id=evaluation_id,
                    name=name,
                    type=labeler_type,
                ),
            )
            for name, values in data_dict.items()
        ]

    id = config.store.write_evaluation_run(serialized_run)

    # Collect summaries for metrics, annotations, and criterion
    summaries = create_summaries(evaluation_run.results.metrics, EvaluationLabelerType.METRIC)
    summaries += create_summaries(evaluation_run.results.annotations, EvaluationLabelerType.ANNOTATION)
    if evaluation_run.results.criterion is not None:
        summaries += create_summaries({"criterion": evaluation_run.results.criterion}, EvaluationLabelerType.CRITERION)

    config.store.write_evaluation_run_labeler_summaries(summaries)

