# Let's define the core types.
from dataclasses import dataclass
from typing import Callable, Dict, List, Union

from typing import Any
from ell.lstr import lstr
from ell.util.dict_sync_meta import DictSyncMeta

_lstr_generic = Union[lstr, str]

OneTurn = Callable[..., _lstr_generic]

# want to enable a use case where the user can actually return a standrd oai chat format
# This is a placehodler will likely come back later for this
LMPParams = Dict[str, Any]


@dataclass
class Message(dict, metaclass=DictSyncMeta):
    role: str
    content: _lstr_generic


# Well this is disappointing, I wanted to effectively type hint by doign that data sync meta, but eh, at elast we can still reference role or content this way. Probably wil lcan the dict sync meta.
MessageOrDict = Union[Message, Dict[str, str]]

# Can support iamge prompts later.
Chat = List[
    Message
]  # [{"role": "system", "content": "prompt"}, {"role": "user", "content": "message"}]

MultiTurnLMP = Callable[..., Chat]
from typing import TypeVar, Any

# This is the specific LMP that must accept history as an argument and can take any additional arguments
T = TypeVar("T", bound=Any)
ChatLMP = Callable[[Chat, T], Chat]

LMP = Union[OneTurn, MultiTurnLMP, ChatLMP]

InvocableLM = Callable[..., _lstr_generic]
