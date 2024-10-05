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

```python
class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    scores: List[Dict[str, float]] = Field(default_factory=list)
    dataset : Dataset = Field(default_factory=list)
    lmp: Optional[LMP] = Field(default=None)
    outputs: List[Any] = Field(default_factory=list)
    api_params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def inputs(self) -> List[Any]:
        return [d['input'] for d in self.dataset]
    

    def write(self, serialized_evaluation_run) -> None:
        # To link!
        pass

class Evaluation(BaseModel):
    """Simple evaluation for prompt engineering rigorously"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    dataset: Dataset
    criteria: Optional[Criteria] = Field(default_factory=dict)
    default_api_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
```

So the chief question here is, what do we do with criteria? In the traditional deviate view criteria are tracked functions And this track functions will appear somehow in the computation graph. And because they adorn The outputs of invocations. We can trace which invocations led to a certain criteria evaluation and then. in the tables for invocations, we can show the criteria as they relate either to an eval or Um an individual invocation that relates them The hard question here is, when we evaluate a criteria, it's based on the output of one particular invocation. So You know, if you show that, for example, in a chain of writing a story where we generate drafts in then generate a final output story, the criteria that are linked downstream of, let's say, generate story ideas as it is realized through writing a story based on those ideas, wouldn't necessarily pipe through on the other end In that we wouldn't probably want to show. That particular metric on the generates story idea evaluation, even though there is sort of a direct line through tracing 

Also, I don't think we really want to show the metrics in the computation graph, but we do want to keep track of them. And it would be simple enough to just have them as sort of functional invocations that are linked. So for example, you could query Was there a invocation that was from an LMP of the type metric that was downstream of this? And then that would be something you show in L studio in the computation graph without creating any additional links, just a simple sql query 

So in this view, we would do the following We metra size all Criteria, or we call them criterion, whatever. L dot criteria, or out. Maybe it would be L dot metric, right? I'm not sure if we want to call them criteria metric yet, but We will adorn With these decorators that basically say, every time it's invoked, we're going to track it. And the it can invoke it any number of times. So like, for example, even MP dot mean would be something that we Adorn like it could be any function from any module. So that's also a little bit weird, right Like, I don't necessarily want to, well, okay, actually, in that case, the source code isn't tracked. The function itself is pickled. So maybe this is okay. Because it's an external module and we need to think about how we serialize external module functions like that, right? Like, if I use a standard eval from some other module, that's just an import. I don't really need to actually serialize like source code for versioning. It's just like fix because we assume the versioning and production versus the versioning here is The The same Period. 

OK, so the total picture so far It is the following. We're going to wrap them in a decorator All their invocations are going to show up in the computation graph. Which is kind of **** actually, because if I literally use something from another module, then I get a ton of invocation. So maybe this is not something I want to do I'm trying to imagine a scenario where that would be the case. Like Yeah, like, imagine we just do like A comparison, right? So like, let's say we have a pre can thing that just like is like L dot. Is equal And then you choose the field that you're trying to be equal to. And you say a criteria equals L is equal of expected output Then every time that he gets called, like basically all the lmps are going to link to that in the graph. I guess we don't particularly have to show that in the graph, but they all do connect on that basis And so now we track, because we're decorating the actual source function, we're going to slow down the invocation of that simple is equal function. So, so much. Whereas I'm not convinced that you want to do the traditional weep thing of decorating the function like when you actually decorate the function on your own like that's going to have a certain cost associated with it So maybe what we do is we allow you to decorate with a metric thing, knowing that if you do decorate with a metric, it Technically be more expensive But the actual realization of this inside of L studio is going to be a little bit different. So if you are passing in a metric. Then. Yeah. So if you're passing in a metric, what's going to happen is that we will use that actual metric function for invocations, and if you're passing in any random function Then we will wrap it in Metric Lambda, which for all intensive purposes will. Do a pass through to the underlying source, but only when we invoke the metric within the criteria. It doesn't take your function and then decorate it, right? Because that's unexpected behavior. In fact, this is just like a wrapper for the purposes of the eval and we literally give the name in the code or within L studio will be like eval dot whatever. And that will be the metric that's being logged, I guess. Okay. So let's say we're now adding that lmp to the computation graph. In L studio, we would differentiate that because Well, I don't know.......


```python
@ell.metric
def my_metric(datapoint, output):
    return output == datapoint['expected_output']

eval = ell.evaluation(name="my_eval", criteria=[my_metric])
```

Does this become:

```
LMPs:
    my_metric
    my_eval.my_metric

Invocations:
    my_metric[0]
    my_eval.my_metric[0]
    my_eval.my_metric[1]
    ...

EvaluationRuns:
    my_eval

```

Yeah, this feels sort of messy, but I also don't like the idea of exceptionalism for metrics when. They are just alfunctions. And that, like, appeared fairly clean on the other side. 


I think one of the bigger problems here is we haven't really solved structured outputs as well, or just arbitrary output parsing I liked the Alex Dixon approach of this, but it wasn't exactly clear that. It would be intuitive to someone you know who's using python. Like, I don't think you can get the return statement of a yield 

Ok. So if you take a look at the yield L pi or md, whatever the document is in rambling, this actually Provides a solution to structure outputs that makes me quite happy. Um, um. And now thinking about it, I think there should actually be A Decorator or something like this. I'm not sure, but um It is now possible to structure outputs and very, very simply. And this is actually a really cool unification of functions and LMP 

OK, so back on this, do we actually wrap? Evaluations In like or the criterion of evaluations in vacations. And we just leave the db schema like very, very clean. I guess the only problem here is this, if I am already like, if I pass in now, let's let's say everything is using yield statements. If I pass in This L dot simple lm thing, or L dot complex lm. And It's already decorated it. then it doesn't make sense to redecorate it. But then now the metric. Doesn't have like a clean, like my eval dot, whatever It's just using some metric I've defined somewhere else in my program. So there is a bit of a problem there. 



Okay and we can just simply solve this by literally creating evaluation criterion or literally just evaluation with like just as a whole object. We don't care about invocations. We don't actually serialize anything and all we're going to do is if you have an LMP score like that just it doesn't matter. It doesn't get written. We don't see it in indication views. We just know that that invocation appeared in eval and then we can go look at the invocation eval run scores and pull. out the score for the L. M. P. From the invocation eval and the score for an L. M. P. And the invocation Eval will look like a table with The invocation Uh the score name or the criterion name the criterion. Id And the Actual float value of the criterion. Along with the invocation run ID. 




Yeah, this feels a bit cleaner, I suppose. But the problem is now Will never have first class support for like these weave ops that we want to log. But of course the. Ultimate score from the lm is now logged. So that's nice.


```
Evaluation Run:
    id
    dataset
    lmp
    outputs
    api_params
    start_time
    end_time

Evaluation Score:
    id
    invocation_id
    evaluation_run_id
    criterion_id
    value

Evaluation Criterion (LMP, but not really; kind of annoying.)
    id
    name
    description
    source
    dependencies
    evaluation_id

Evaluation:
    id
    name
    dataset
```


Now if we use LMP

```
Evaluation Run:
    id
    dataset
    lmp_id
    evaluation_id
    outputs
    api_params
    start_time
    end_time

Evaluation Score:
    id
    criterion_lmp_id
    evaluation_run_id
    evaluation_id # redundant
    value

Criterion:
    id
    lmp_id
    name #as defined by the criteria.
    evaluation

Evaluation:
    id
    name
    dataset
    (criteria)
    (runs)

```

in this case


```python

class Evaluation(BaseModel):
    criteria: Dict[str, Callable]
    dataset: Dataset
    name: str

    def __init__(self, name: str, dataset: Dataset, criteria: Dict[str, Callable]):
        wrapped_criteria = {
            name: ell.metric(criterion) for name, criterion in criteria.items()
        }
        self.criteria = wrapped_criteria

@ell.simple(model="gpt-4o")
def write_a_poem(topic : str):
    response = yield f"Write a poem about {topic}"
    return response

# EVAL CRITERION!!!

@ell.simple(model="gpt-4o")
def is_good_poem(datapoint, output):
    response = yield f"Is this a good poem? {output}"
    return "yes" in response.lower()

@ell.simple(model="gpt-4o")
def on_topic(datapoint, output):
    response = yield [
        ell.system("You are a helpful assistant. Always answer with 'yes' or 'no'."),
        ell.user(f"Is this poem about {datapoint['topic']}? {output}")
    ]
    return "yes" in response.lower()


eval = Evaluation(name="my_eval", dataset=poem_prompt_dataset, criteria={
    "matches_expert_poem": lambda datapoint, output: output == datapoint['expert_poem'], 
    "is_good": is_good_poem,
    "on_topic": on_topic,
})

eval.run(write_a_poem)
```
