====================================
Evaluations (New)
====================================

Evaluations represent a crucial component in the practice of prompt engineering. They provide the quantitative and qualitative signals necessary to understand whether a language model program achieves the desired objectives. Without evaluations, the process of refining prompts often devolves into guesswork, guided only by subjective impressions rather than structured evidence. Although many developers default to an ad hoc process—manually reviewing a handful of generated outputs and deciding by intuition whether one version of a prompt is better than another—this approach quickly becomes untenable as tasks grow more complex, as teams grow larger, and as stakes get higher.

The premise of ell’s evaluation feature is that prompt engineering should mirror, where possible, the rigor and methodology of modern machine learning. In machine learning, progress is measured against validated benchmarks, metrics, and datasets. Even as one tunes parameters or tries novel architectures, the question “Did we do better?” can be answered systematically. Similarly, evaluations in ell offer a structured and reproducible way to assess prompts. They transform the process from an ephemeral art into a form of empirical inquiry. In doing so, they also introduce the notion of eval engineering, whereby evaluations themselves become first-class entities that are carefully constructed, versioned, and refined over time.


The Problem of Prompt Engineering by Intuition
----------------------------------------------

Prompt engineering without evaluations is often characterized by subjective assessments that vary from day to day and person to person. In simple projects, this might suffice. For example, when producing a handful of short marketing texts, a developer might be content to trust personal taste as the measure of success. However, as soon as the problem grows beyond a few trivial examples, this style of iterative tweaking collapses. With more complex tasks, larger data distributions, and subtle constraints—such as maintaining a specific tone or meeting domain-specific requirements—subjective judgments no longer yield consistent or reliable improvements.

Without evaluations, there is no systematic way to ensure that a revised prompt actually improves performance on the desired tasks. There is no guarantee that adjusting a single detail in the prompt to improve outputs on one example does not degrade outputs elsewhere. Over time, as prompt engineers read through too many model responses, they become either desensitized to quality issues or hypersensitive to minor flaws. This miscalibration saps productivity and leads to unprincipled prompt tuning. Subjective judgment cannot scale, fails to capture statistical performance trends, and offers no verifiable path to satisfy external stakeholders who demand reliability, accuracy, or compliance with given standards.

.. note::

   The intuitive, trial-and-error style of prompt engineering can be visually depicted. Imagine a simple diagram in ell Studio (ell’s local, version-controlled dashboard) that shows a single prompt evolving over time, each modification recorded and compared. Without evaluations, this “diff” of prompt versions tells us only that the code changed—not whether it changed for the better.


The Concept of Evals
--------------------

An eval is a structured evaluation suite that measures a language model program’s performance quantitatively and, when necessary, qualitatively. It consists of three essential elements. First, there is a dataset that represents a distribution of inputs over which the prompt must perform. Second, there are criteria that define what constitutes a successful output. Third, there are metrics that translate the model’s raw outputs into a measurable quantity.

Below is a minimal example showing how these pieces fit together in ell. Assume we have a dataset of simple classification tasks and a language model program (LMP) that attempts to answer them:

.. code-block:: python

    import ell
    ell.init(store="./logdir")  # Enable versioning and storage

    # 1. Define an LMP:
    @ell.simple(model="gpt-4o", max_tokens=10)
    def classify_sentiment(text: str):
        """You are a sentiment classifier. Return 'positive' or 'negative'."""
        return f"Classify sentiment: {text}"

    # 2. A small dataset:
    dataset = [
        {"input": {"text": "I love this product!"}, "expected_output": "positive"},
        {"input": {"text": "This is terrible."}, "expected_output": "negative"}
    ]

    # 3. A metric function that checks correctness:
    def accuracy_metric(datapoint, output):
        return float(datapoint["expected_output"].lower() in output.lower())

    # 4. Constructing the eval:
    eval = ell.evaluation.Evaluation(
        name="sentiment_eval",
        dataset=dataset,
        metrics={"accuracy": accuracy_metric}
    )

    # Run the eval:
    result = eval.run(classify_sentiment)
    print("Average accuracy:", result.results.metrics["accuracy"].mean())

Here, the dataset provides two test cases, the LMP attempts to solve them, and the metric quantifies how well it performed. As the LMP changes over time, rerunning this eval yields comparable, reproducible scores.

In many cases, constructing an eval means assembling a carefully chosen set of input examples along with ground-truth labels or ideal reference outputs. For tasks that resemble classification, defining metrics is straightforward. For more open-ended tasks, evals may rely on heuristic functions, human annotations, or even other language model programs (critics) to rate outputs.


Eval Engineering
----------------

Defining a single eval and sticking to it blindly can be as problematic as never evaluating at all. In practice, an eval is never perfect on the first try. As the prompt engineer tests models against the eval, new edge cases and overlooked criteria emerge. Perhaps the chosen metric saturates too easily, or perhaps the dataset fails to represent the complexity of real inputs. Updating and refining the eval in response to these insights is what we call eval engineering.

Consider a scenario where our first eval always returns a perfect score. Maybe our criteria are too lenient. With eval engineering, we revise and strengthen the eval:

.. code-block:: python

    # A new, more complex metric that penalizes incorrect formatting:
    def stricter_accuracy(datapoint, output):
        # Now we require the output to match exactly 'positive' or 'negative'
        # to count as correct, making the eval more discriminative.
        return float(output.strip().lower() == datapoint["expected_output"].lower())

    # Revised eval:
    eval_strict = ell.evaluation.Evaluation(
        name="sentiment_eval_stricter",
        dataset=dataset,
        metrics={"accuracy": stricter_accuracy}
    )

    # Run on the same LMP:
    result_strict = eval_strict.run(classify_sentiment)
    print("Average accuracy (stricter):", result_strict.results.metrics["accuracy"].mean())

If the original eval gave an average accuracy of 1.0, the stricter eval might yield a lower score, prompting further improvements to the LMP. Over time, eval engineering leads to evaluations that genuinely reflect the underlying goals.


Model-Based Evaluation
--------------------------------

In many real-world scenarios, an eval cannot be reduced to a fixed set of rules or ground-truth answers. Consider a task like producing compelling outreach emails. Quality is subjective, and the notion of success might be tied to subtle attributes. In these cases, one can incorporate human judgments or another LMP as a critic:

.. code-block:: python

    @ell.simple(model="gpt-4o")
    def write_invitation(name: str):
        """Invite the given person to an event in a friendly, concise manner."""
        return f"Write an invitation for {name} to our annual gala."

    # A critic that uses an LMP to check if the invitation is friendly enough:
    @ell.simple(model="gpt-4o", temperature=0.1)
    def invitation_critic(invitation: str):
        """Return 'yes' if the invitation is friendly, otherwise 'no'."""
        return f"Is this invitation friendly? {invitation}"

    def friendly_score(datapoint, output):
        # Run the critic on the output
        verdict = invitation_critic(output).lower()
        return float("yes" in verdict)

    dataset_invites = [
        {"input": {"name": "Alice"}},
        {"input": {"name": "Bob"}},
    ]

    eval_invites = ell.evaluation.Evaluation(
        name="friendly_invitation_eval",
        dataset=dataset_invites,
        metrics={"friendliness": friendly_score},
    )

    result_invites = eval_invites.run(write_invitation)
    print("Average friendliness:", result_invites.results.metrics["friendliness"].mean())

Here, we rely on a second LMP to measure friendlier invitations. If its judgments are too lenient or too strict, we can “eval engineer” the critic as well—refining its instructions or training a reward model if we have human-labeled data. Over time, these improvements yield more robust and meaningful evaluations.

In particular, one can construct an eval for their eval, period. In order to generate a critic that reliably mirrors human judgments, you can first create a dataset of your own qualitative assessment of various LLM outputs you wish to create an eval for. In order to generate a critic that reliably mirrors human judgments, you can first create a dataset of your own qualitative assessment of various LLM outputs you wish to create an eval for.


Connecting Evals to Prompt Optimization
---------------------------------------

By placing evaluations at the center of prompt engineering, the entire process becomes more efficient and credible. Instead of repeatedly scanning outputs and making guesswork judgments, the prompt engineer tweaks the prompt, runs the eval, and compares the scores. This cycle can happen at scale and against large datasets, providing statistically meaningful insights.

For example, suppose we want to improve the `classify_sentiment` LMP. We make a change to the prompt, then rerun the eval:

.. code-block:: python

    # Original prompt in classify_sentiment:
    # "You are a sentiment classifier. Return 'positive' or 'negative'."
    # Suppose we revise it to include a stricter definition:

    @ell.simple(model="gpt-4o", max_tokens=10)
    def classify_sentiment_improved(text: str):
        """You are a sentiment classifier. If the text shows positive feelings, return exactly 'positive'.
        Otherwise, return exactly 'negative'."""
        return f"Check sentiment: {text}"

    # Re-run the stricter eval:
    result_strict_improved = eval_strict.run(classify_sentiment_improved)
    print("Stricter accuracy after improvement:", result_strict_improved.results.metrics["accuracy"].mean())

If the new score surpasses the old one, we know we have made a meaningful improvement. Over time, multiple runs of these evals are recorded in ell’s store. They can be visualized in ell Studio (a local, dashboard-like interface) to track progress, identify regressions, and compare versions at a glance.


Versioning and Storing Evals in ell
-----------------------------------

Just as prompt engineering benefits from version control and provenance tracking, so does eval engineering. An eval changes over time: new datasets, new metrics, new criteria. ell captures these changes automatically when `ell.init()` is called with a storage directory. Each run of an eval stores results, metrics, and associated prompts for future reference.

You can open ell Studio with:

.. code-block:: bash

    ell-studio --storage ./logdir

Here, you will see your evals listed alongside their version histories, their datasets, and the results produced by various LMP runs. This environment allows both prompt engineers and eval engineers to confidently iterate, knowing that any improvement or regression can be traced back to a specific version of the prompt and the eval.


Accessing and Interpreting Evaluation Results
---------------------------------------------

After running an eval, ell provides an `EvaluationRun` object, which stores both raw outputs and computed metrics. You can access these as follows:

.. code-block:: python

    run = eval_strict.run(classify_sentiment_improved)
    # Access raw metrics:
    metrics = run.results.metrics
    print("All metrics:", metrics.keys())
    print("Accuracy scores per datapoint:", metrics["accuracy"].values)

    # Access raw outputs:
    print("Model outputs:", run.results.outputs)

This structured data makes it straightforward to integrate evaluations into CI pipelines, automatic regression checks, or advanced statistical analyses.


The Underlying API for Evaluations
----------------------------------

The `Evaluation` class in ell is flexible yet straightforward. It handles dataset iteration, calling the LMP, collecting outputs, and applying metric and annotation functions. Its interface is designed so that, as your tasks and methodology evolve, you can easily incorporate new data, new metrics, or new eval configurations.

A simplified version of the `Evaluation` class conceptually looks like this:

.. code-block:: python

    class Evaluation:
        def __init__(self, name: str, dataset=None, n_evals=None, samples_per_datapoint=1, metrics=None, annotations=None, criterion=None):
            # Initialization and validation logic
            self.name = name
            self.dataset = dataset
            self.n_evals = n_evals
            self.samples_per_datapoint = samples_per_datapoint
            # Wrap metrics and criteria and store them internally
            # ...

        def run(self, lmp, n_workers=1, use_api_batching=False, api_params=None, verbose=False, **additional_lmp_params):
            # 1. Prepare dataset and parameters
            # 2. Invoke the LMP on each datapoint
            # 3. Compute metrics and store results
            # 4. Return EvaluationRun with all information
            return EvaluationRun(...)

This API, combined with ell’s built-in tracing, versioning, and visualization, provides a complete solution for rigorous prompt engineering and eval engineering workflows.

As evals grow and mature, they provide the stable foundation on which to stand when refining prompts. Combined with ell’s infrastructure for versioning and tracing, evaluations make it possible to bring principled, data-driven methodologies to prompt engineering. The result is a process that can scale in complexity and ambition, confident that improvements are real, documented, and reproducible.