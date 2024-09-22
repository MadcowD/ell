# How do we want to handle model adaptation..
# I don't really want to maitnain some base registry and update it every damn time a new model comes out, but it's not clear how we specify providers otherwise.

# e.g.


@ell.simple(model="gpt-4-turbo", temperature=0.1)
def blah():
    pass


# Even then Azure is bullshit and doesn't use the same model names as oai so we cant really even have a registry. I guess we could do best effort and occasionally updat ehte lbirary when new models come out?
@ell.simple(model="gpt-4-turbo", provider=AzureProvider, temperature=0.1)
def blah():
    pass



# Do we make each provider implement several types of supported interfaces?

class Provider(abc.ABC):
    def __init__

    pass


# I mean OAI has basically set the standard for how all providers in teract.
class OAILikeProvider(abc.ABC):


# Also do we care about tracking embeddings?
# no not yet lol, but we clearly nee a generic invocation stack.

# We can just focus on text output models for now and revisit later if necessary.

# Wow that was ass 


# Am I really going to expect my users to pass around the same 'client' class to all the models.. Also since this is inthe decorartor they'd have to define this client globally. I also want thigns to be mostly static; there's not really a reason to reinstantiate these providers. Except for changing the 'client'


# the only reaosn for the client is to enable switching between different model infra bakcends for oai lol rather than hard coding ours.
# we could also jsut adopt oai's philosophy on this and just use their cliejts as our providers class. but i hate the idea that i have to pass clients around all the time for different mdoe lclasses.



# this is very much a user decision and in fact you might even want to load balance (a la azure not implementing this..)
register('gpt-4-turbo', oai_client)
register('llama-70b-chat', groq_client)


# how to balance this with low barrirer to entry. env vars didnt' work last time. 

# some amount of initialization of the library needs to happen at the beginning.
# this is a requirement in that while we could just default to oai models from oai and attempt to use the oai client on first invocation of an lmp
ell.init(
    oai_client=...,
)

# okay so by default we will use the standard provider of a model if a model is 'standard' from a provider ie llama can get fucked but 4 turbo we'll go w oai
# we will try to initialize using the env vars for dany defauly provider but essentially we need to prvoide a runtime interface for a user to select which provider they want to use for a class of mdoels.
# im fine using my own fucking client..

# would there ever be a situation when the user wants to switch between clients for different lmps
# rate limits etc.

# i really didnt want to make this my job but now it's my job.

# ew
"""ell.set_provider(
    models=ell.providers.OpenAI.models,
    provider=ell.providers.Azure
)"""

# or...
# we could go entirely functional

# fuck conflict resolution
""ell.register('gpt-4-turbo', OpenAI.chat)
""

# inherently you just don't want to fuck around with

""blah(api_params=dict(client=my_openai_client))
""
# or even

with ell.use_client(my_openai_client): #<-- well maybe actually i like this
    blah()

# or even
with_client(blah, openai)()


# it might be as simple as saying: "Just implement the oai standard and you're good to go.."

# should see how one atualyl invokes mystral etc.
# brb

"""
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"

client = MistralClient(api_key=api_key)

messages = [
    ChatMessage(role="user", content="What is the best French cheese?")
]

# No streaming
chat_response = client.chat(
    model=model,
    messages=messages,
)
"""

"""from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
)
"""

# As much as I like the with_client framework, it does't actually relegate a certain model to a certain provider.

# We could get django about htis shit



class ProviderMeta():
from typing import List, Type

from ell.types.message import MessageOrDict

class ProviderMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if hasattr(cls, 'models'):
            cls.register_models(cls.models)

    @staticmethod
    def register_models(models):
        for model in models:
            print(f"Registering model: {model}")





class OAILikeProvider(Provider):
    models = [
        "gpt-4-turbo"
    ]
    @staticmethod
    def chat_completions(client, model, messages : List[MessageOrDict]):
        client.chat.completions.create(
            model=model,
            messages=messages
        )

OAIProvider = OAILikeProvider
# Ah so this is weird: We actually might have providers with different model classes that we want to specify  for example, azure doesn't have defualt names for these models and they are in the user namespace... So literally when we want to use an azure provier we have 'isntantiate it'. That's fucking annoying lol. 

# For example we'd actually want the user to be able to easily switch to gpt-4-turbo without changing all their lmp code.
AzureProvider(
    model_map = {
        oai.GPT4Turbo: "ell-production-canada-west-gpt4-turbo"
    }
)

# and azure is so fucked that i'm pretty sure you need to specify different clients for different regions..
# :( 

# just adopt the oai standard :\ please. this hurts.
# Like the model map is per client. So now we can't even disambiguate providers and model maps.


# Mistral had to be special didn';t it;;
class MistralProvider(Provider):
    models = [
        "some trash model"
    ]

    def chat(client, model, message):
        chat_response = client.chat(
        model=model,
        messages=messages,
    )


# then we handle conflict resolution:
# "Two providers have registered this mdoel, you msut specify a provider."

# Basically we don't handle the client ptoblem but we do handle the code mismatch problem

# So really it'll also be per model.