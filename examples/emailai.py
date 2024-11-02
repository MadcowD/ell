from pydantic import BaseModel
import ell
import time
import ell.evaluation

ell.init(verbose=True, store="./logdir")

class Person(BaseModel):
    name: str
    job_title: str
    linked_in_bio: str

CRITERION = """
- There has to be a plausible reason as to why they are being contacted
- The email should be on the basis of selling something.
- The email needs to explciitly say or mention who the sender is and why they are contacting them. 
- The reason should be on the basis of something in the real persons profile.
- There should be format strings or symbals like { in the } email.
"""

@ell.simple(model="o1-preview")
def would_the_person_respond_critic(email, real_person):
    return [
#         ell.system(
#             f"""
# Would the person respond to this email? 
# Answer in the following format:

# `<Chain of thought reasoning as to why you would believe the person would respond or not>
# Answer: <yes or no>`
# Criterion:
#             {CRITERION}
#             """
#         ),
        ell.user(f"""Would the person respond to this email? 
Answer in the following format:

`<Chain of thought reasoning as to why you would believe the person would respond or not>
Answer: <yes or no>`
Criterion:
            {CRITERION} Email: {email}\n\n Cold Outreach target: {real_person.model_dump_json()}"""),
    ]


def would_the_person_respond(email, real_person):
    return "answer: yes" in would_the_person_respond_critic(email, real_person).lower()

criterion = lambda datapoint, output: would_the_person_respond(output, datapoint['input'][1])

@ell.simple(model="gpt-4o")
def write_email(fake_ai_person, real_person):
    return [
        ell.system(f"""
    Write an email to a given person that would be convincing enough for them to repsond.
    You will be provided your profile and the profile of the person you are writing a cold email to.
    
Important Rules:
- Never include a subject.
- Your email should be at most two sentences.
- Never write words that are logner than 5 charachters
{CRITERION}
"""),
        ell.user(f"You: {fake_ai_person.model_dump_json()}\n\n Cold Outreach target: {real_person.model_dump_json()}")
    ]

import ell.lmp.function
@ell.lmp.function.function()
def write_best_email(fake_ai_person, real_person, api_params=None):
    five_emails = write_email(fake_ai_person, real_person, api_params=(dict(n=10)))
    for email in five_emails:
        if would_the_person_respond(email, real_person):
            return email
    return "failure"
    


example_person = Person(
    name="Sarah Chen",
    job_title="VP of Engineering",
    linked_in_bio="Engineering leader with 15+ years experience scaling distributed systems. Currently VP of Engineering at Stripe leading the Payments Infrastructure team. Previously Engineering Director at Netflix where I led the Content Delivery Network team. MS in Computer Science from Stanford. Passionate about building high-performing engineering teams and mentoring the next generation of technical leaders."
)

example_ai_person = Person(
    name="Ell",
    job_title="Business Development Manager",
    linked_in_bio="Business development professional with 8+ years experience in enterprise software sales and partnerships. Previously led strategic partnerships at Salesforce and Oracle. Proven track record of building long-term relationships with Fortune 500 clients and driving revenue growth. MBA from Berkeley Haas School of Business. Passionate about connecting innovative solutions with business needs."
)



eval = ell.evaluation.Evaluation(
    name="sounds_humamn",
    dataset=[
        dict(input=[example_ai_person, example_person]),
    ],
    samples_per_datapoint=10,
    metrics={
        "length": lambda _, output: len(output),
        "word_length": lambda _, output: sum(len(word) for word in output.split()) / len(output.split()),
        "sentence_count": lambda _, output: len([s for s in output.replace('!', '.').replace('?', '.').split(".") if s.strip()]),
    },
    criterion=criterion,
    
)


if __name__ == "__main__":
    eval.run(write_best_email, n_workers=10)
    # print(email)




# Be able to see the outputs of the criterion function as it used in the eval.
# esc bug on tables
# the hash od the data changes because are hashing the pickle and not the serialzied data soruce.