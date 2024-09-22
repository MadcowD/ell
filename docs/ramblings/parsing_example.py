import dataclasses
import random
from typing import Callable, List, Tuple
import ell
from ell.types._lstr import _lstr




# Option 0 (pythonic.)
# This going to be NON Native to ell

def parse_outputs(result : _lstr) -> str:
    name = result.split(":")[0]
    backstory = result.split(":")[1]
    return Personality(name, backstory)


@ell.simple(model="gpt-4o-mini", temperature=1.0, output_parser=parse_outputs)
def create_random_personality():
    """You are backstoryGPT. You come up with a backstory for a character incljuding name. Choose a completely random name from the list. Format as follows.

Name: <name>
Backstory: <3 sentence backstory>'""" # System prompt

    return "Come up with a backstory about " + random.choice(names_list) # User prompt


def get_personality():
    return parse_outputs(create_random_personality())

# Option 1.

def parse_outputs(result : _lstr) -> str:
    name = result.split(":")[0]
    backstory = result.split(":")[1]
    return Personality(name, backstory)


@ell.simple(model="gpt-4o-mini", temperature=1.0, output_parser=parse_outputs)
def create_random_personality():
    """You are backstoryGPT. You come up with a backstory for a character incljuding name. Choose a completely random name from the list. Format as follows.

Name: <name>
Backstory: <3 sentence backstory>'""" # System prompt

    return "Come up with a backstory about " + random.choice(names_list) # User prompt



## Option 2.

@dataclasses.dataclass
class Personality:
    name : str
    backstory : str

    @staticmethod
    def parse_outputs(result : _lstr) -> str:
        name = result.split(":")[0]
        backstory = result.split(":")[1]
        return Personality(name, backstory)

@ell.simple(model="gpt-4o-mini", temperature=1.0, output_parser=Personality.parse_outputs)
def create_random_personality():
    """You are backstoryGPT. You come up with a backstory for a character incljuding name. Choose a completely random name from the list. Format as follows.

Name: <name>
Backstory: <3 sentence backstory>'""" # System prompt

    return "Come up with a backstory about " + random.choice(names_list) # User prompt


# Option 3. Another decorator

def parse_outputs(result : _lstr) -> str:
    name = result.split(":")[0]
    backstory = result.split(":")[1]
    return Personality(name, backstory)

@ell.structure(parser=parse_outputs, retries=3)
@ell.simple(model="gpt-4o-mini", temperature=1.0)
def create_random_personality():
    """You are backstoryGPT. You come up with a backstory for a character incljuding name. Choose a completely random name from the list. Format as follows.

Name: <name>
Backstory: <3 sentence backstory>'""" # System prompt

    return "Come up with a backstory about " + random.choice(names_list) # User prompt



create_random_personality: Callable[..., Personality]


# This really boils down to what is the role of ell
# Are there high level Keras like braries that use our low level primatives.


# if we say that it also provides high level functionality:

class PersonalitySchema(ell.Schema):
    name : str
    backstory : str

    def parse_outputs(result : _lstr) -> str:
        name = result.split(":")[0]
        backstory = result.split(":")[1]
        return Personality(name, backstory)

@ell.structured_lm(
    schema=PersonalitySchema,
    model="gpt-4o-mini",
    temperature=1.0,
)
def create_random_personality():
    """You are backstoryGPT. You come up with a backstory for a character incljuding name. Choose a completely random name from the list. Format as follows.""" # System prompt

    return "Come up with a backstory about " + random.choice(names_list) # User prompt

# under the hood this mutates the system promtp of create random.


# https://python.langchain.com/v0.1/docs/modules/model_io/output_parsers/quick_start/
# Optiona 5. Langchain verison of this with ell


# or 
def parser(result : _lstr) -> OutputFormat:
    name = result.split(":")[0]
    backstory = result.split(":")[1]
    return OutputFormat(name, backstory)


# 3. Define our LM we can use the format from our schema or something else
@ell.structures(parserer=parser, retries=3)
@ell.simple(model="gpt-4o-mini", temperature=1.0)
def create_random_personality():
    f"""Answer in the format {OutputFormat.get_format_prompt()}"""

    return "Come up with a backstory about " + random.choice(names_list)


def f(arg = None, * , lol=3, **kwargs):
    print(arg, lol, kwargs)
    pass


#############################
#############################

# These first two violate our strict storage schema.


def parser(pstr):
    name = pstr.split("name:")[1].split("\n")[0].strip()
    backstory = pstr.split("backstory:")[1].split("\n")[0].strip()

    return name, backstory

@ell.structure(parserer=parser, retries=3)
@ell.simple(model="gpt-4o-mini", temperature=1.0)
def create_random_personality():
    f"""Answer in the format {format}"""

    return "Come up with a backstory about " + random.choice(names_list)

############################
############################


@ell.simple(model="gpt-4o-mini", temperature=1.0)
def create_random_personality_str():
    f"""Answer in the format {format}"""

    return "Come up with a backstory about " + random.choice(names_list)


@retry(tries=3)
def get_random_personality():
    pstr = create_random_personality_str()
    json.parse(pstr)
    name = pstr.split("name:")[1].split("\n")[0].strip()
    backstory = pstr.split("backstory:")[1].split("\n")[0].strip()


    return pstr


#############################
#############################


def parser(pstr):
    name = pstr.split("name:")[1].split("\n")[0].strip()
    backstory = pstr.split("backstory:")[1].split("\n")[0].strip()

    return name, backstory

@ell.simple(model="gpt-4o-mini", temperature=1.0, parser=parser)
def create_random_personality():
    f"""Answer in the format {format}"""

    return "Come up with a backstory about " + random.choice(names_list)





"""
Authors notes: I think if we dont implement parsing, people can build lightweight opinionated libraries on top of ell for parsing.

Langchain could be built on top of ell (?)

ell

# all python packages that we could build that dont effect ell as a library.

ell-agents
ell-structure


The whole conversation ultimatels boils down to if we decide to store strucutred data in the ell.db. 

If I have
"""
@ell.simple(model="gpt-4o-mini", temperature=1.0, parser=parser)
def create_random_personality():
    f"""Answer in the format {format}"""

    return "Come up with a backstory about " + random.choice(names_list)

"""
And now I wrap it in my parser:
"""

def parse_to_my_fucked_up_unserializable_format(pstr):
    return MyFuckedUpObject(pstr)

@ell.structure(parser=parse_to_my_fucked_up_unserializable_format, retries=3)
@ell.simple(model="gpt-4o-mini", temperature=1.0)
def create_random_personality():
    f"""Answer in the format {format}"""

    return "Come up with a backstory about " + random.choice(names_list)

"""
Now when I run this program what appears in the database? Do we attempt to store the MyFuckedObject instance in the ell.db as a result of the invocation of the LMP.

Is there a utility to doing so. Do we have two types of invocations
(I look graph and there is a node for create random personality and I can expadn it and look inside and there are two nodes tracing to each other:)

(create_personality) -> parse_to_my_fucked_unserializable_format


This is equivalent to the following
"""
@ell.simple(model="gpt-4o-mini", temperature=1.0)
def create_random_personality():
    return "Come up with a backstory about " + random.choice(names_list)

@ell.track
@retry(tries=3)
def parse_to_my_fucked_up_unserializable_format(pstr):
    return MyFuckedUpObject(pstr)


@ell.track
def get_fucked_up_llm_object():
    return parse_to_my_fucked_up_unserializable_format(create_random_personality())

# Lol langchain is the following:
get_fucked_up_llm_object = ell.track(create_random_personality | parse_to_my_fucked_up_unserializable_format)

"""
What hapopens when we can't serialize MyFuckedUpObject. We build the best dill dumper into our db of these objects.
"""

# Build a hand holdy structured_lm framework
# structured_lm@v0.1.0
# description = 'allows you to prompt engineer llms that attempt to conform to schemas using state of the art prompt techniques'

"""
This is same quesiton as do we have ell.cot or is ell-cot a package
cot_llm = ell.cot(
    task=""
)
"""

# base prompt override!
@structured_lm.json(RPGSchema, model='gpt-4o-mini', temperature=1.0):
def make_a_rpg_character(name : str):
    return f"Make a rpg character that slaps. They should be called {name}"

"""
What the this does is:
"""
# structured_lm.py
def json(schema : ell.Schema,**api_params):
    def decorator(func):
        def converted_lm_func():
            system_prompt, user_prompt =  func()
            new_system_prompt = [
                system_prompt + " You must respond only in JSON in the following format: " + schema.get_format_prompt(),
                user_prompt
            ]
            return new_system_prompt, user_prompt

        return retry(schema.parse(
            ell.simple(**api_params)(converted_lm_func)), tries=3)
        
    return decorator

# This does this:

@ell.simple(model="gpt-4o-mini", temperature=1.0)
def internal_make_a_rpg_character(name : str):
    return [
        ell.system("You are a rpg character creator. You create rpg characters. You must respond only in JSON in the following format: " + {RPGSchema.get_format_prompt()}),
        ell.user(f"Make a rpg character that slaps. They should be called {name}")
    ]


@ell.track
@retry(tries=3)
def parse(result : _lstr):
    return json.parse(result)


@ell.track
def make_a_rpg_character(name : str):
    return result(internal_make_a_rpg_character(name))



