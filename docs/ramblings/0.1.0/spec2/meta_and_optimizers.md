# Different meta prompt formats

```python
@ell.meta(model="gpt-4")
def write_blog_post(topic: str) -> BlogPost:
    """
    Write a detailed and engaging blog post about the given topic.
    """
    pass  # Or contains arbitrary code

# Alternative 2
write_blog_post = ell.meta(
    input={"topic": str},
    output=BlogPost,
    instructions="Write a detailed and engaging blog post about the given topic.",
    model="gpt-4"
)

# Using the function
blog_post = write_blog_post(topic="Artificial Intelligence")
```

```python
from dataclasses import dataclass

@dataclass
class BlogPost:
    title: str
    content: str

@ell.function(model="gpt-4")
def write_blog_post(topic: str) -> BlogPost:
    """
    Write a detailed and engaging blog post about the given topic.
    """
    # Optional arbitrary code
    topic = topic.capitalize()

    # Use ell.auto_prompt with output_type
    return ell.auto_prompt(topic=topic, output_type=BlogPost)

# View the generated prompt
print(write_blog_post.prompt_template)

# Optimize the prompt
optimizer = ell.FewShotOptimizer()
optimized_write_blog_post = optimizer.fit(
    write_blog_post,
    x=["Artificial Intelligence", "Climate Change"],
    y=[
        BlogPost(title="The Future of AI", content="..."),
        BlogPost(title="Addressing Climate Change", content="...")
    ]
)

# Use the optimized function
blog_post = optimized_write_blog_post("Quantum Computing")
print(blog_post.title)
print(blog_post.content)
```


```python
@ell.meta(model="gpt-4")
def write_blog_post(topic: str):
    return ell.Prompt(
        instructions="Write a detailed and engaging blog post about the given topic.",
        inputs={"topic": topic},
        outputs={"title": str, "content": str}
    )
```

# Optimizer Specs

```python

@ell.simple(model="gpt-4")
def analyze_sentiment(text: str):
    # Arbitrary code to preprocess text
    processed_text = preprocess_text(text)
    return [
        ell.system("You are a sentiment analysis assistant."),
        ell.user(f"Determine the sentiment of the following text:\n{processed_text}")
    ]

# Define the optimizer
optimizer = ell.FewShotOptimizer()

# Fit the optimizer with training data
optimized_analyze_sentiment = optimizer.fit(
    analyze_sentiment,
    x=["I love this!", "I hate this!"],
    y=["Positive", "Negative"]
)

# Use the optimized function
result = optimized_analyze_sentiment("I'm not sure about this product.")

# Inspect the optimized prompt
print(optimized_analyze_sentiment.optimized_prompt)
```


# Structured outputs?

Necessity and arbitrary parsing
```python
@ell.simple(model="gpt-4")
def write_an_email(recipient: str, topic : str, tone : str):
    return [
        ell.system("You are a helpful assistant that writes emails. Format your output as Subject: <subject>\nBody: <body>."),
        ell.user(f"Write an email to {recipient} about {topic} in a {tone} tone."),
    ]


@ell.function()
def write_an_email_parsed(recipient: str, topic : str, tone : str) -> Tuple[str, str]:
    y = other_random_code() 
    email_unparsed = write_an_email(recipient, topic, tone) + y
    subject = email_unparsed.split("\n")[0].split("Subject: ")[1]
    body = email_unparsed.split("\n")[1].split("Body: ")[1]
    retuen (subject, body)

bootstrapped_fewshot_optimizer = ell.FewShotOptimizer()

good_eamil_examples_X = [
    ("mom", "dinner was good", "excited"),
    ("john smith", "i need a new project", "formal"),
]

good_eamil_examples_Y = [
    ("Dinner was fantastic!", "Thank you for having me over last night. The food was incredible. I'm still full thinking about it!"),
    ("Looking for a new project", "I'm looking for a new project to work on. Do you have any ideas?"),
]

@ell.simple(model="gpt-4")
def loss_was_close_to_output(output, target):
    """You are extremely sensitive to determining if the output is close to the target. You return a number between 0 and 1"""
    return f"{output}\n{target}\n\nIs the output close to the target? Return a number between 0 and 1."


fewshot_optimizer.fit(
    write_an_email,
    x=good_eamil_examples_X,
    y=good_eamil_examples_Y,
    loss_fn=lambda y_pred, y_target: loss_was_close_to_output(y_pred, y_target),
)


# This requires write_an_email_parsed^-1

# Need to insert 
```


You can few shot ell.simpel you can't few shot ell.function because you can't inver the fucntion even if you did it approxiamtely it would be wrong.


```python
@ell.simple("o1-preview")
def approximate_label(label: str, non_invertible_source :str,  prompt_function_name :str, ):
    return f"""
We are trying to guess what output of {prompt_function_name} would elucidate the the label data
after being processed by <non_invertible_source>.  

<non_invertible_source>
{non_invertible_source}
</non_invertible_source>

<label>
{label}
</label>
```




```python
@ell.simple(model="gpt-4o")
def my_initial_prompt(instructions : str) -> str:
    return f"{ell.learnable("You must write a blog post about the following topic:")} {instructions}"



opt = ell.Optimizer()

opt.fit(my_initial_prompt, x=x, y=y)



```


opt.fit(write_email_parsed, "make the emails shoerter please")