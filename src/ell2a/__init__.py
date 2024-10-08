"""
ell2a is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""


from ell2a.lmp.simple import simple
from ell2a.lmp.tool import tool
from ell2a.lmp.complex import complex
from ell2a.types.message import system, user, assistant, Message, ContentBlock
from ell2a.__version__ import __version__

# Import all models
import ell2a.providers
import ell2a.models


# Import everything from configurator
from ell2a.configurator import *
