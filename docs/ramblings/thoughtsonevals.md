# Evals & Metrics

We need to build a really good evals and metrics functionality for ell so that prompt engineering becomes more rigorous. This should be extremely approachable for a startup or a person from a non-ML background, but with high quality and rigorous statistical analysis built in. It should work naturally with ell studio. It should be fast. It should be easy.

We can either design this by coming from the ML background and thinking of the traditional train, test, and validation set loss function for a particular model. I think this is probably useful. But then there's also a bit of UX around the actual iteration loop, where we iterate in concert with changes to versions of various different prompts. We store those iterations over time. And then beyond that typical workflow, we should also consider different types of evals that are not metric-based. There are reward model-based evals, critic-based evals (I'll categorize those as the same), zero-one accuracy evals, and then vibe evals. In my own use case, the vibe evals were probably the most relevant, and those are somewhat harder to assess and make functional for the end user. But I can envision a world where you modify your prompt, you define a set of inputs, and then we enable the user in ell studio to very quickly compare inputs and outputs between versions in a blind fashion. This automatically generates comparison data. It also generates an implicit RLHF dataset and lets you rigorously compare between versions instead of the typical workflow of living in Jupyter notebook and looking at the outputs of one change versus the next. We would then want to build a bunch of guides to get people used to this workflow and this is a great introduction to optimizers as well.

There are a number of features we could build here that might also be interesting. So these are just evaluations which are good for the prompt engineering workflow. They fundamentally have versions themselves, and those versions are a form of data versioning. But we could also consider things like metrics and runs. So what is that particularly in the prompt engineering use case? That looks something like we were doing a prompt engineering session, and I want to iterate on a prompt for one session. So I spin up a run and then I can track the quality of the iteration on that prompt over that run. So this would be the evals and other metrics. This is kind of similar to MLflow runs and actually is somewhat solved for by having the logger, so you don't have to use the same logger over and over again. So this is something we probably don't need to focus on implementing. We just need to think about evals and metrics. But this would effectively allow you to organize versions or prompt engineering sessions or optimizations as runs, and you can look at loss curves and things like this. This is probably extremely important.

The next thing we would care about: So evals use metrics. Metrics are ways of just like the same probably as TensorBoard metrics, which is that they are collections of XY plot data, histograms, and so on that can be tied to particular ell objects. Would we ever want a world where we tied a metric to an invocation? Let's say we had user feedback. So we could log for every invocation, you know, if there was feedback from the user, you could log it to ell studio. And then in ell studio, you could look at the average feedback for a version or other summary statistics on that. This requires implementation of a very nice plotting library. But yeah, metrics could be logged at any point in time, and they could be tied to any type of invocation. The question is, do we want to sort of automatically tie them? So what's an example of this? The metric is just a number tied to an invocation or tied to an LMP, and so in fact you can plot metrics over any different X axis: time, version, and so on.

Now we have automatic tracing. And we also have the notion of how do we define a metric. So we have to introduce all of the underlying ell Studio data types or can we just automatically do this? Are metrics only for invocations and LMPs? So what if I just want to log like a random float? It's kind of like MLflow or TensorFlow, right? Like first step, for example. You could totally do that. So there's like two interfaces. There are metrics that are associated with LMPs and classes of metrics there, as well as metrics that are just floating. They need to be associated to something, they'll probably be like a run. Because, in fact, TensorBoard does this even with the same TensorBoard storage directory, right? Every time you connect a TensorBoard, you get a new run. It might be the instance of the process, or something like this. Or you could hard code the run ID. So yeah, there's a lot of different concepts here. Let's recap.

We have evals, which are easy to run, parallelized dataset runs of an LMP or a function associated with various metrics, and that are versioned themselves. We have metrics which are ways of keeping track of various numbers associated to invocations or LMPs. And then we might also have metrics that are not associated with anything.

We need to disambiguate and square all of these concepts so that we can come up with a design spec for a really clean interface and ell. Some context here is that ell is a language model programming framework, or prompt engineering framework, which basically enables rapid iteration of prompts on a local machine or in production. And we need to nail this metric and evaluation interface so that prompt engineering becomes extremely easy and rigorous.



### Ramblings on the interface

```python
# Would be cool if it opened a UI for you to watch the run as it was going down.


eval = Evaluation(
        name="test",
        inputs=dataset,
        labels=dataset,
        metric=ell.eval.accuracy
)

# all of the nice scikit learn stuff on rpedictors
# Examples of different evals.
score = ell.eval.accuracy(predict_capital, inputs=dataset[:,0 ], labels=dataset[:,1], name="accuracy")
score = ell.eval.mean_squared_error(predict_capital, inputs=dataset[:,0 ], labels=dataset[:,1], name="mse")
score = ell.eval.r2_score(predict_capital, inputs=dataset[:,0 ], labels=dataset[:,1], name="r2")


# An example of why we need ot fix input outptu format
@ell.simple(model="gpt-4o", temperature=0.0)
def critic_fn(input: str, output: str):
    """Answer only with 'yes' or 'no'."""
    return f"Is the following output correct? {output} given the input: {input}"

@ell.function()
def critic_score(input: str, output: str):
    return float(critic_fn(input, output) == "yes")


# @ell.function()
# def critic_fn(input: str, output: str):
#     output = ell.simple(model="gpt-4o", temperature=0.0)(f"I said {output} to the following input: {input}. Is that correct? ")
#     return output == "yes"

print(ell.eval.eval(predict_capital, inputs=dataset[:,0 ], score=critic_score))



class Metric(Protocol):
    def __call__(self, input : Any, output : Any, label : Optional[Any]) -> float:
        ...

    def vectorizedcall(self, inputs : List[Any], output: List[Any], labels : Optional[List[Any]] = None) -> List[float]:
        ...


Evaluation(
    name="test",
    inputs=dataset,
    labels=dataset, # optionally
    metrics=[
        ell.eval.accuracy,
        critic_score
    ]
)
```



Counter point is metric don't effect the version of an eval if we view evals as datasets.
```python
eval.run 
scikitlearn.metrics.accuracy_score(
    predictor,
    x = dataset[:,0],
    y = dataset[:,1]
    "asd",
    

eval = Evaluation(
    name="linkedinprofiles",
    inputs=dataset[:,0],
    labels=dataset[:,1],
)

# This is a problem with the eval.run interface
{ [0.5, 0.5], [0.5, 0.5] } = eval.run(my_lmp, metrics=[
    ell.eval.accuracy,
    critic_score
]) # y_pred

accuracies = ell.eval.accuracy(y_pred, x = dataset[:,0], y = dataset[:,1])
critic_scores = ell.eval.critic_score(y_pred, x = dataset[:,0], y = dataset[:,1], critic_fn=critic_fn)

print(accuracies.mean())
print(critic_scores.mean())



@ell.simple(model="gpt-4o")
def write_cold_email(input: str):
    return f"Write a cold email to the following person: {input}"

# most impoeritive case
ell.evaluate(
    "linkedin profiles",
    write_cold_email,
    inputs=dataset[:,0],
    labels=dataset[:,1],
    metrics=[
        ell.eval.accuracy,
        critic_score
    ]
) 
# Options:
-> [
    {
        "accuracy": 0.5,
        "critic_score": 0.5
    },
    {
        "accuracy": 0.5,
        "critic_score": 0.5
    }
]
-> [
    [0.5, 0.5],
    [0.5, 0.5]
]
-> EvaluationRun(
    scores = [
        [0.5, 0.5],
        [0.5, 0.5]
    ],
    inputs = dataset[:,0],
    labels = dataset[:,1],
    metrics = [
        ell.eval.accuracy,
        critic_score
    ]
)


# OR:
Evaluation(
    name="linkedin profiles eval",
    inputs=dataset,
    labels=dataset, # optionally
    metrics=[
        ell.eval.accuracy,
        critic_score
    ]
)

eval.run(write_cold_email) -> (any of the above outptus)


run.metrics.critic_score
# im gonna version this for you 




@ell.metric()
def accuracy(y_pred, y_true):
    return np.mean(np.array(y_pred) == np.array(y_true))

def eval():
    with ell.run("linkedin profiles eval", verbose=False):
        from concurrent.futures import ThreadPoolExecutor
        import numpy as np

        def process_datapoint(x, y):
            out = write_cold_email(x)
            return accuracy(y_pred=out, y_true=y)

        with ThreadPoolExecutor() as executor:
            scores = list(executor.map(process_datapoint, dataset[:,0], dataset[:,1]))

        scores = np.array(scores)
        print(scores.mean())
        ell.log_summary("critic_score", scores.mean())


### OR ###

eval() 


# combine with evals
# naive metrics are not a part of evals.

eval = Evaluation(
    name="linkedin profiles eval",
    inputs=dataset[:,0],
    labels=dataset[:,1],
)

outputs = eval.run(write_cold_email) # cold emails
scores = []
for x, y,out in zip(dataset[:,0], dataset[:,1], outputs):
    scores.append(accuracy(y_pred=out, y_true=y))

print(scores.mean())
ell.log_summary("avg accuracy", scores.mean())

def v(inputs, labels, outputs):
    scores = []
    for x, y,out in zip(inputs, labels, outputs):
        scores.append(accuracy(y_pred=out, y_true=y))
    ell.log_summary("avg accuracy", scores.mean())
    return scores

eval = Evaluation(
    name="linkedin profiles eval",
    inputs=dataset[:,0],
    labels=dataset[:,1],
    score = callback
)

scores = eval.run(write_cold_email)




# Supporting promtp engineering of metrics themeselves,



@ell.simple(model="gpt-4o")
def evaluate_email(cold_email: str):
    """ You are an empath who is extremely good at evaluating cold emails. You are given a cold email and you must determine if it is good or bad. You will evaluate the cold email on the following criterion:
    
    A good cold email is:
    - Concise < 5 sentences
    - Personalized to the recipient
    - Extremely non generic (it must be unique to the sender.
  
Your outptu should be in the following format: 
Analysis: <5 paragraphs of analysis>
Score of email quality: <1-10>
Is good cold email: <yes/no yes if score is 8 or higher>
    """
    return f"Is the following cold email good for the following person: {cold_email}"


@ell.retry(max_retries=3)
@ell.metric()
def is_good_cold_email(x : str):
    analysis=  is_the_cold_email_good(x)
    is_good_cold_email = analysis.split("Is good cold email: ")[1] == "yes"
    return float(is_good_cold_email)





dataset = Dataset(
    name="linkedin profiles",
    inputs=dataset[:,0],
)

ell.init(run="linkedin profiles eval", store="./logdir", verbose=True, tags=["cold-email", "linkedin"])


[[1,1], [0,1]] = dataset.evaluate(write_cold_email, n_workers=4, metrics=[is_good_cold_email, accuracy])

ell.log_summary("avg accuracy", outputs[:,1].mean())
ell.log_summary("avg is_good_cold_email", outputs[:,0].mean())



outputs = eval.run(write_cold_email)
eval.score(write_cold_email, metric=accuracy)
# list[float]
```


How do we square the following interface:
```python

run = ell.run("linkedin profiles eval")
# or
ell.init(experiment="linkedin profiles eval", store="./logdir", verbose=True, tags=["cold-email", "linkedin"])
# or


# Logs if it can be traced.
@ell.metric()
def accuracy(y_pred : _lstr , y_true) -> float:
    return np.mean(np.array(y_pred) == np.array(y_true))

scores = []
for x,y in dataset:
    out = write_cold_email(x)
    scores.append(accuracy(y_pred=out, y_true=y))

print(scores.mean())
ell.log("cirtic_score", scores.mean())
```

```python

eval = Evaluation(
    name="linkedin profiles eval",
    inputs=dataset[:,0],
    labels=dataset[:,1],
    metric = callback
)

outputs = ell.parallel(write_cold_email, inputs=dataset, n_workers=4)
score = np.array(ell.parallel(is_good_cold_email, outputs, n_workers=4))
print(score.mean())

evalrun = eval.run(write_cold_email)

evalrun.scores
evalrun.outputs


```


```python

dataset = ...
@ell.metric()
def accuracy(y_pred, y_true):
    return (np.array(y_pred) == np.array(y_true))

500 predicions -> accuracy all ofthem get the same accuracy metric.

def eval(n_workers=4):
    with ell.run("linkedin profiles eval", verbose=False):
        from concurrent.futures import ThreadPoolExecutor
        import numpy as np

        outputs = ell.parallel(write_cold_email, inputs=dataset, n_workers=n_workers)
        
        scores = accuracy(outputs, dataset[:,1])
        ell.log("accuracy", scores)
        
        print(scores.mean())
        ell.log_summary("critic_score", scores.mean())

eval() 

### OR ###
@ell.metric()
def accuracy(y_pred, y_true):
    return np.mean(np.array(y_pred) == np.array(y_true))

dataset = ...
eval = Evaluation(
    name="linkedin profiles eval",
    inputs=dataset[:,0],
    labels=dataset[:,1],
    metric=accuracy
)

eval.run(write_cold_email, n_workers=4
)

### OR ####

dataset = [...]

@ell.eval("linkedin profiles eval")
def eval(lmp : ell.LMP):
    outputs = ell.parallel(lmp, inputs=dataset, n_workers=4)

    scores = accuracy(outputs, dataset[:,1])
    ell.log("accuracy", scores.mean())
    return scores, outputs, "num chars" + str(sum([len(x) for x in outputs]))

eval(write_cold_email)


## Discovery. Metrics are inadequate for describingi indivudal scores afforded to invocations.

class Metric(Protocol):
    def __call__(self, input : List[Any], output : List[Any], label : Optional[List[Any]] = None) -> float:
        """Produces a aggregate metric."""
        ...


# With this example how do we solve adding more metrics on?

 # X, ypred, ytrue -> float.
metric  = Callable[[List[Any], List[Any], Optional[List[Any]]], float]

def accuracy(y_pred, y_true):
    return np.mean(np.array(y_pred) == np.array(y_true))

dataset = ...
eval = Evaluation(
    name="linkedin profiles eval",
    inputs=dataset[:,0],
    labels=dataset[:,1],
    metric=accuracy
)

run = eval.run(write_cold_email, n_workers=4)

run.scores # list[float]
run.result # float

# recall
y_pred, y_true = run.outputs, run.labels
print(ell.metrics.recall(y_pred, y_true))


# This is bad. 

eval = Evaluation(
    name="linkedin profiles eval",
    inputs=dataset[:,0],
    labels=dataset[:,1],
    metrics=dict(
        accuracy=ell.metrics.accuracy,
        recall=ell.metrics.recall,
        critic_score=ell.metrics.critic_score
    )
)

run = eval.run(write_cold_email, n_workers=4)

run.scores # list[float]
run.result['accuracy'] # list[float]
run.result['recall'] # list[float]
run.result['critic_score'] # list[float]


# 1. We would want to introduce the following:
# Evaluation (heleper)
# Evaluation Run

# Metric (always aggregrated)
# Grouping.
 # Evaluatio induces a grouping.


#%%

# WHat does aggregate reward model look like?


@ell.simple(model="gpt-4o")
def evaluate_email(cold_email: str):
    """ You are an empath who is extremely good at evaluating cold emails. You are given a cold email and you must determine if it is good or bad. You will evaluate the cold email on the following criterion:
    
    A good cold email is:
    - Concise < 5 sentences
    - Personalized to the recipient
    - Extremely non generic (it must be unique to the sender.
  
Your outptu should be in the following format: 
Analysis: <5 paragraphs of analysis>
Score of email quality: <1-10>
Is good cold email: <yes/no yes if score is 8 or higher>
    """
    return f"Is the following cold email good for the following person: {cold_email}"


def quality_score(y_pred : List[Any], y_pred : Optional[List[Any]] = None) -> float:
    analyses = ell.parallel(evaluate_email, y_pred, n_workers=4)    
    is_good_cold_email = [float(analysis.split("Is good cold email: ")[1] == "yes") for analysis in analyses]
    return np.mean(is_good_cold_email)


ell.metricize(quality_score) # No.
```
### Conclusion

1. Evaluations
    - Evaluatio nclass
    - Versioned datasets
    - Versioned "metrics"
2. Runs (groupds of invocations)
3. Metric is an **aggregate** statistic on a potentially labeled dataset.
    - This is scikit learn metrics interface.

Which are runs along with versioned datasets and metrics

## Run vs Interprocess Execution.
Interprocess executions versus runs. Currently, we have evaluations that run on a single process, and those evaluations consist of groups of individual evaluation runs. These evaluation runs are single-process and linked to evaluations. We could envision a scenario where we want to run evaluations or group runs across multiple processes. For instance, let's say I track scores of my evaluations as I perform a prompt engineering process on a thesis. I want to group my runs or invocations by, for example, an emotional empathy thesis. If I'm building a cold email writer, this grouping would be useful.

The only way to effectively flag this would be to make The init function Specify the current experiment or some such similar flag 
```
ell.init(experiment="emotional empathy", store='./logdir)
```

The tree would look like this:
```
experiment[emotional-empathy] ->
    run[leap-for-the-sky-o6] -> # process 1
        invocation[cold-email-1]
        invocation[cold-email-2]
        invocation[cold-email-3]
    run[leap-for-the-sky-o7] -> # process 2
        invocation[cold-email-1]
        invocation[cold-email-2]
        invocation[cold-email-3]
    run[leap-for-the-sky-o8] -> # process 3
        invocation[cold-email-1]
        invocation[cold-email-2]
        invocation[cold-email-3]
```


With an eval we get

```
experiment[emotional-empathy] ->
    evaluation[cold-email-writer] ->
        evaluation run | 
        run[leap-for-the-sky-o6] -> # no logner correspodns to a single process execution.
            invocation[cold-email-1]
            invocation[cold-email-2]
            invocation[cold-email-3]
        evaluation run | 
        run[leap-for-the-sky-o7] ->
            invocation[cold-email-1]
            invocation[cold-email-2]
            invocation[cold-email-3]
```

In general automatically grouping by "run" Is a bad thing when we think about The production execution with multiple process brokers and processes. 

We can just have experiment labeling as a convenience function where. otherwise We don't label by experiment. And also, this doesn't make sense, necessarily, for production runs as well. 

In that case. We might end up with something that looks like this 

```
experiment[emotional-empathy] ->
    evaluation[cold-email-writer] ->
        evaluation run | 
        run[leap-for-the-sky-o6] -> # no logner correspodns to a single process execution.
            invocation[cold-email-1]
            invocation[cold-email-2]
            invocation[cold-email-3]
    invocation[cold-email-4]
    invocation[cold-email-5]
invocation[cold-email-6] # happened in dev
invocation[cold-email-7] # happened in production
invocation[cold-email-8]
```

We don't necessarily need to solve this in this PR. If we can just build an abstraction that works for evaluations and individualized metrics without thinking about per-invocation scores, adding that later, then we would be happy. I suppose we could take a look at the open AI eval suite and then go from there, just to see if they do scoring per invocation. We could additionally just have an invocation score, and that would be many-to-many. You can score invocations in many different ways. For evals, you build a metric function which takes in a bunch of invocations and labels, and then produces an aggregated metric that is one-to-one with evaluations. We version those metrics. We support individual invocation scores in this PR as a part of the individual changes to the DB schema as well as migrations. But otherwise, don't opinionate the implementation, and we end up with schemas for evaluations and evaluation runs independent of experiments. In fact, this is probably sufficient.

The question would be whether or not we separate evaluation runs and run groupings of invocations, or do we just tie invocations directly to evaluations? If we were to introduce runs as a full-fledged feature within experiments, or something like this later, then we would have sort of a legacy evaluation runs thing that we need to get rid of later.


### OpenAI Evals
It is evident that OpenAI evaluations support multiple metrics by default. An interesting aspect is their criterion specification. Overall the UX is lacking. No ability to see the outputs of individual invocations (perhaps this is what happens if you share the evals with OpenAI etc.).


Probably not a good model for our evals but:
1. Test Data
   - Import a JSONL file with existing cases or prompts.

2. Generate Responses
   - Generate responses (Optional)
   - Prompt
   - Generated responses can be evaluated using the sample.output_text variable within testing criteria.


3. Criterion (multiple)
   a. Factuality
      - Check if the content is factually accurate.
   b. Semantic Similarity
      - Compare generated text to the reference.
   c. Sentiment
      - Identify the emotional tone of the model’s response.
   d. String Check
      - Check if the model’s response includes specific string(s).
   e. Valid JSON or XML
      - Check if the model’s response is valid JSON or XML.
   f. Matches Schema
      - Ensure the model’s response follows the specified structure.
   g. Criteria Match
      - Assess if the model’s response matches your criteria.
   h. Text Quality
      - Assess response quality with BLEU, ROUGE, or Cosine algorithms.
   i. Custom Prompt
      - Create a test criterion by writing your own custom prompt.
  
Concrete recommendations for our case are as follows: we want pre-canned criteria and having per-invocation criteria seems to be important for evaluations. It is also important to note that most of these evaluations are done by models, which is how OpenAI prefers to run them. In our case, we are not designing evaluations for individual per-invocation criteria, but rather aggregate metrics to be more in line with scikit-learn and similar frameworks. 

If we were to go in the opposite direction and support per-invocation criteria, allowing arbitrary datasets in an evaluation and providing a programmatic API for OpenAI-like invocations, it might be worthwhile. If I were to envision that API shape, it would look like the following:



```python
def criterion1(datapoint):
    input = datapoint[0]
    output = datapoint[1]
    return float(output == "yes")


@ell.simple(model="gpt-4o-mini")
def was_gramatically_correct(datapoint):
    return f"Did the following cold email have any gramatical errors? {datapoint[1]}. Answer with yes or no."

def criterion2(datapoint):
    return float( "yes" in was_gramatically_correct(datapoint).lower())

evaluation = Evaluation(
    name="cold-email-evaluation",
    dataset=dataset,
    criterion=[
        criterion1,
        criterion2,
        criterion3
    ]
)

evaluation.run()
```

What's really weird about this is that it's completely dependent on a dataset of input-output pairs and it doesn't rerun on the same prompt, which is effectively the goal of evaluations in DSP.

We could kind of re-envision this. If we think about one part of the OpenAI evals, you were allowed to generate a response on top of a dataset, and that's the kind of thing we'll put here. So the dataset will include all the output labels, and then we have a generate response function that takes in some data point and then generates responses as a result of that. But then the user has to index into what would be the correct input. By allowing datasets to have arbitrary data points in them, including the labels and arbitrary columns, just think about them as JSON objects. Then you can have criteria that fit all sorts of different settings, right? So I could have inputs, I could have 100 different labels, and I can assess the total criterion of everything. And then I can think about pass/fail in general. And that might actually be the right thing to do. So let's imagine now we have response generation as a key component.

```python

def criterion1(datapoint, output):
    input = datapoint['input']
    desired_output = datapoint['output']
    desired_sentiment = datapoint['desired_sentiment']

...


evaluation = Evaluation(
    name="cold-email-evaluation",
    dataset=dataset, # pandas dataframe??
    criterion=[
        criterion1,
        criterion2,
        criterion3
    ]
)


evaluation.run(
    my_lmp
)

This works for criterion but itsn ot clear what input the LMP should take.
We could seperate out input and output into two seperate columns.


evaluation = Evaluation(
    name="cold-email-evaluation",
    dataset=dataset, # pandas dataframe??
    labels=label_dataset,
    criterion=[
        criterion1,
        criterion2,
        criterion3
    ]
)

@ell.simple(model="gpt-4o-mini")
def my_lmp(datapoint):
    # Columns of the input dataset are the args to mylmp?
    # How would  would I  actually want this in practice ?
    pass


evaluation.run(
    my_lmp 
)
```



Weave does a much better job at orgnaizing this. There opinion is the following


```python
dataset = Dataset(
    [
        {"some_random_shit" : "some_value", "expected_output" : "some_value", "other_column" : "other_value"},
        {"some_random_shit" : "some_value", "expected_output" : "some_value", "other_column" : "other_value"},
        {"some_random_shit" : "some_value", "expected_output" : "some_value", "other_column" : "other_value"},
    ]
)

```

Now this data set automatically gets versioned.

```python
eval = Evaluation(
    name="my_evaluation",
    dataset=dataset,
    scores=[
        score1,
        score2,
    ]
```


So you basically define scorers, and they will automatically extract the relevant. columns from the data set based on the inspected parameter arguments.

```python

def score1(expected_output, output):
    return np.mean(np.array(expected_output) == np.array(output))

def score2(other_column, output):
    return np.mean(np.array(expected_output) == np.array(output))

args = inspect.signature(score1).parameters

...

class Evaluation:
    def run():
        results = {}
        for datapoint in self.dataset:
            for score in self.scores:
                args = inspect.signature(score).parameters
                datapoint_subset = {k : datapoint[k] for k in args}
                score_output = score(**datapoint_subset)
                results[score.__name__].append(score_output)

```


I do like the idea of being able to publish a dataset. I think we should have parity there. I do like that evaluations are automatically versioned in some sense. We should also have parity there.

I'm not convinced that the shape of the evaluation function should look like Model output, etc. Also, the model evaluation itself doesn't seem very clean, right? If I'm developing an LMP that I'm going to use somewhere else in my software stack, and I want to evaluate it, now I have to wrap it in some additional function. This layer of indirection between me and the evaluation might cause failure later. The fundamental data shape of the evaluation should be kind of like whatever I'm always using in my LMPs plus labels. I don't want to think about inputs versus outputs in my criterion. The input data shape is holy, and in some sense, I don't want to have to change the LMP's source code just because my input data shape has changed. As for scoring functions, yeah, I think there's some convenience in being able to pull out from the rows of a dataset. In that way, it makes sense. Also, look how clean it is to specify datasets like that. It is beautiful what we've done there, though the Thursday AI guys are not going to like that I've changed this in the way that I have.

Also, datasets fundamentally are very weird. If they only exist for the purpose of evals, then maybe the abstraction doesn't make any sense. We can do a lot of things with datasets, right? We can fine-tune on them. The traditional ML literature doesn't exactly make sense for the RL use case, which is where we want to head with this. So I think by developing a dataset abstraction now, we're going to cause problems later when we decide to do RL on prompts and things of this nature.

So let's suppose we just ignore the traditional dataset abstraction for now, right? And so we ship evals as a feature. Evals as a feature just have inputs and outputs. Now, the problem with inputs and outputs, right? When I was actually doing stuff in production with these models, we would take in many times non-serializable objects. I don't want the user to have to think about whether or not their object is truly JSON serializable. But it's not clear exactly how we would define the dataset if it weren't just unpacking some sort of dictionary into the kwargs, right? The shape always has to be a dictionary, and the other convenience function of having datasets where the labels and the inputs and outputs are in line. People are very used to working that way. So if we had separate inputs and outputs, they would have to zip these together, which doesn't make a lot of sense. Okay, but we can be magical like Weaviate. 

When you define the dataset, you do rows of dictionaries, where rows correspond to named kwargs of your LMP. Again, the named kwargs thing is actually bad because certain LMPs are also positional. So being able to swap in an LMP and another LMP, one that uses slightly different named kwargs, will totally break the process. So that's not acceptable. What we can do is serialize sort of positional and non-positional named kwargs in the dataset formulation. Each row can contain an input object, and that input object is either a list or a dictionary. You can name the kwargs or not. It's probably a bad idea to name the kwargs because then you can't swap in different LMPs. Then we always use the inputs here. And this is just typed dicts. I guess we have a type dictionary. And we always use that. Then the rest of the outputs, you can do whatever you want. Your score function will take in the row and the model output. What Weaviate did was they literally said, "Hey, your thing has to accept model output as a kwarg." So they validate the score functions by inspecting keyword arguments. Then everything's wrapped in a Weaviate op because that Weaviate ops automatically log to wandb. So they unify the interface of logging in that way.

```python

# Example implementation based on the ideas discussed

from typing import List, Dict, Any, Union, Callable
import inspect
import numpy as np

# Define a flexible Dataset type
Dataset = List[Dict[str, Any]]

# Example dataset
dataset: Dataset = [
    {"input": "What is the capital of France?", "expected_output": "Paris", "difficulty": "easy"},
    {"input": "What is the square root of 144?", "expected_output": "12", "difficulty": "medium"},
    # ... more data points
]

# Example LMP (Language Model Program)
def my_lmp(input: str) -> str:
    # This is a mock LMP that just returns the input
    return input

# Example score functions
def accuracy_score(expected_output: str, output: str) -> float:
    return float(expected_output.lower() == output.lower())

def difficulty_weighted_score(difficulty: str, expected_output: str, output: str) -> float:
    base_score = float(expected_output.lower() == output.lower())
    difficulty_weight = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
    return base_score * difficulty_weight.get(difficulty, 1.0)

class Evaluation:
    def __init__(self, name: str, dataset: Dataset, lmp: Callable, scores: List[Callable]):
        self.name = name
        self.dataset = dataset
        self.lmp = lmp
        self.scores = scores

    def run(self) -> Dict[str, List[float]]:
        results = {score.__name__: [] for score in self.scores}
        
        for datapoint in self.dataset:
            # Run the LMP
            lmp_input = datapoint.get("input")
            if isinstance(lmp_input, str):
                output = self.lmp(lmp_input)
            elif isinstance(lmp_input, dict):
                output = self.lmp(**lmp_input)
            elif isinstance(lmp_input, list):
                output = self.lmp(*lmp_input)
            else:
                raise ValueError(f"Unsupported input type: {type(lmp_input)}")
```
Alright, so this part is a bit too magical. Essentially, what it's doing is taking the input object and, if it's a single object, passing it directly into the LMP. Otherwise, it destructures the arguments. I do appreciate the use of **kwargs versus list destructuring; it's quite elegant. We can think of it as handling both args and kwargs, which is fine. However, it's also quite clean to write your dataset as single input elements.

```python
            # Calculate scores
            for score in self.scores:
                args = inspect.signature(score).parameters
                datapoint_subset = {k: datapoint.get(k) for k in args if k != 'output'}
                score_output = score(**datapoint_subset, output=output)
                results[score.__name__].append(score_output)

        return results

# Usage example
eval = Evaluation(
    name="my_evaluation",
    dataset=dataset,
    lmp=my_lmp,
    scores=[accuracy_score, difficulty_weighted_score]
)

results = eval.run()
print(results)

# You could then add methods to analyze and visualize the results
# For example:
def analyze_results(results: Dict[str, List[float]]):
    for score_name, scores in results.items():
        print(f"{score_name}:")
        print(f"  Mean: {np.mean(scores):.4f}")
        print(f"  Median: {np.median(scores):.4f}")
        print(f"  Min: {np.min(scores):.4f}")
        print(f"  Max: {np.max(scores):.4f}")

analyze_results(results)

```

So now let's consider The usability of these input shapes. If we're really going to accept that, there's like some special input data point arg.


```python
class DatapointPD(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    input : Dict[str, Any] | List[Any]
    labels: Dict[str, Any]


# or

class DatapointTD(TypedDict, total=False):
    input : Dict[str, Any] | List[Any]

# finally
Dataset = List[Datapoint]


# This is actually quite in the style of ell where we have input and output in ell studio as either a list of arguments or a dictionary of kwargs.
dataset = [
    Datapoint(input=["What is the capital of France?"], labels={"expected_output": "Paris"}),
]

# or
dataset = [
    {"input" : {'question' : "What is the capital of France?"}, "answer" : "Paris"},
]
#/equivalently
dataset = [
    DatapointTD(input=["What is the capital of France?"], labels={"expected_output": "Paris"}),
]

```

This approach is quite elegant. We need to use Pydantic models with `total=False` so we can validate that each entry has an input.

Imagine defining a dataset in this structured way, where every entry must at least have the shape of an input. You can then add arbitrary fields to the dataset columns. This avoids the issue where the shape of the LMP function needs to be transformed.

So let's actually write out what the final form of this might actually look like and see if it's palatable. If it's not that's okay.
```python


@ell.simple(model="gpt-4o-mini")
def write_a_poem(about :str):
    """You are PoetGPT.  You always write in iambic pentameter. Only answer with a poem."""
    return f"Write a poem about {about}"


@ell.simple(model="gpt-4o-mini")
def iambic_pentameter(poem :str):
    return f"Is the following poem in iambic pentameter? {output} answer with yes or no."


# This is like OpenAI + weave evals.

eval = Evaluation(
    name="poem-eval",
    dataset=[
        Datapoint(input=["a rose"], must_contain="rose", minimum_length=100),
        Datapoint(input=["a sunset"], must_contain="sunset", minimum_length=100),
        Datapoint(input=["a rainbow"], must_contain="", refuse=True, minimum_length=100),
    ],
    criterion=[
        lambda datapoint, output: datapoint.must_contain in output,
        lambda datapoint, output: len(output) >= datapoint.minimum_length,
        lambda datapoint, output: "I refuse to write a poem about that" in output or not datapoint.refuse,
        lambda datapoint, output: "yes" in iambic_pentameter(output).lower(),
    ]
)


eval.run(write_a_poem)
# a set of scores.
# Then we modify write a poem



@ell.simple(model="gpt-4o-mini")
def write_a_poem(about :str):
    """You are PoetGPT.  You always write in iambic pentameter. Only answer with a poem. Say I refuse to write a poem about that if you are asked to write about rianbows """
    return f"Write a poem about {about}"


# Now the refusal criterion will work.
eval.run(write_a_poem)

# Now we improve iambic pentameter score by trying to rewrite the poem.

@ell.simple(model="gpt-4o-mini")
def better_poem_writer(about :str):
    """You are a poet. You are a poet who is extremely good at writing iambic pentameter. If the poem says I refuse just copy the refusal"""
    initial_poem = write_a_poem(about)

    return f"Rewrite the following poem in iambic pentameter: {initial_poem}"


eval.run(better_poem_writer)
# highest score.

```

I think I like this Eval the most from any of the specs I have come up with. You can just throw accuracy criteria in there. It's very easy by specifying how the dataset looks. The Weave guys definitely built a really good abstraction here. Some small changes around where things feel magical make this pretty close to an abstraction that we can use. In the above example, it's extremely readable as to what's going on, and I can imagine a very simple flow where I iteratively improve things. I don't have to worry about what's going on with the individual args or kwargs, as they're specified in the input dict. If there's a mismatch, then I just use arguments instead of kwargs. As for the criterion, you just take in the data point and the output. It's just two positional arguments. The data point is literally just what came from the dataset. So if you ever need to look at the schema, it's all there. Inputs are separated out. Inputs are a requirement for data points. We can validate that when we build the eval. This is a very particular type of dataset, and this lets you very quickly and rapidly develop fast evaluations.

The only problem here is I think what is very nice about the OpenAI evaluation product is that it comes with tons of evaluations by default. For example, text similarity, text quality, BLEU score, things like this. And because the dataset is so free, we don't have an expected output. We can't run metrics automatically.

We could, by default, actually include something inside the metric functionality, like a special keyword in the dataset. If we actually use the reserved expected output keyword, then you can just use pre-canned metrics without having to specify them, because then we're sort of moving the transmutation of metrics to the criterion specification, right? But I could automatically run things like BLEU score or text similarity if you use the expected output keyword. Otherwise, I guess we could just make them instantiable, so I might actually prefer this. So let's just do this, for example.


```python


from ell.evals import cosine_similarity

@ell.simple(model="gpt-4o-mini")
def write_a_poem(about :str):
    """You are PoetGPT. Write with cheesy well-known poems if available."""
    return f"Write a poem about {about}"


eval = Evaluation(
    name="poem-eval",
    dataset=[
        # jsonl injection into dataset formula
        Datapoint(input=["a rose"], expert_poem="Roses are red, violets are blue, sugar is sweet, and so are you.")
    ],
    criterion=[
        cosine_similarity("text-embedding-3-small", expected_output="expert_poem", inner_product="normal")
    ]
)

# can automatically do cosine similarity & other nice things
eval.run(write_a_poem)

```


