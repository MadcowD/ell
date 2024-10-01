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


ell.metricize(quality_score)

```python

### Conclusion

1. Evaluations
    - Evaluatio nclass
    - Versioned datasets
    - Versioned "metrics"
2. Runs (groupds of invocations)
3. Metric is an **aggregate** statistic on a potentially labeled dataset.


Which are runs along with versioned datasets and metrics





