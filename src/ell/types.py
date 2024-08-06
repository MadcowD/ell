# Let's define the core types.
from dataclasses import dataclass
from typing import Callable, Dict, List, Union

from typing import Any
from ell.lstr import lstr
from ell.util.dict_sync_meta import DictSyncMeta

from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlmodel import Field, SQLModel, Relationship, JSON, ARRAY, Column, Float

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


def utc_now() -> datetime:
    """
    Returns the current UTC timestamp.
    Serializes to ISO-8601.
    """
    return datetime.now(tz=timezone.utc)


class SerializedLMPUses(SQLModel, table=True):
    """
    Represents the many-to-many relationship between SerializedLMPs.
    
    This class is used to track which LMPs use or are used by other LMPs.
    """

    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)  # ID of the LMP that is being used
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)  # ID of the LMP that is using the other LMP



class SerializedLMP(SQLModel, table=True):
    """
    Represents a serialized Language Model Program (LMP).
    
    This class is used to store and retrieve LMP information in the database.
    """
    lmp_id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the LMP, now an index
    name: str = Field(index=True)  # Name of the LMP
    source: str  # Source code or reference for the LMP
    dependencies: str  # List of dependencies for the LMP, stored as a string
    created_at: datetime = Field(default_factory=utc_now, index=True)  # Timestamp of when the LMP was created
    is_lm: bool  # Boolean indicating if it is an LM (Language Model) or an LMP
    lm_kwargs: dict  = Field(sa_column=Column(JSON)) # Additional keyword arguments for the LMP

    invocations: List["Invocation"] = Relationship(back_populates="lmp")  # Relationship to invocations of this LMP
    used_by: Optional[List["SerializedLMP"]] = Relationship(
        back_populates="uses",
        link_model=SerializedLMPUses,
        sa_relationship_kwargs=dict(
            primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id",
            secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id",
        ),
    )
    uses: List["SerializedLMP"]  = Relationship(
        back_populates="used_by",
        link_model=SerializedLMPUses,
        sa_relationship_kwargs=dict(
            primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id",
            secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id",
        ),
    )

    # Bound initial serialized free variables and globals
    initial_free_vars : dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars : dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Cached INfo
    num_invocations : Optional[int] = Field(default=0)
    commit_message : Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)
    
    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]



class InvocationTrace(SQLModel, table=True):
    """
    Represents a many-to-many relationship between Invocations and other Invocations (it's a 1st degree link in the trace graph)

    This class is used to keep track of when an invocation consumes a in its kwargs or args a result of another invocation.
    """
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)  # ID of the Invocation that is consuming another Invocation
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)  # ID of the Invocation that is being consumed by another Invocation


class Invocation(SQLModel, table=True):
    """
    Represents an invocation of an LMP.
    
    This class is used to store information about each time an LMP is called.
    """
    id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the invocation
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id", index=True)  # ID of the LMP that was invoked
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))  # Arguments used in the invocation
    kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))  # Keyword arguments used in the invocation

    global_vars : dict = Field(default_factory=dict, sa_column=Column(JSON))  # Global variables used in the invocation
    free_vars : dict = Field(default_factory=dict, sa_column=Column(JSON))  # Free variables used in the invocation

    latency_ms : float 
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    state_cache_key: Optional[str] = Field(default=None)

    
    created_at: datetime = Field(default_factory=utc_now)  # Timestamp of when the invocation was created
    invocation_kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))  # Additional keyword arguments for the invocation

    # Relationships
    lmp: SerializedLMP = Relationship(back_populates="invocations")  # Relationship to the LMP that was invoked
    # Todo: Rename the result shcema to be consistent
    results: List["SerializedLStr"] = Relationship(back_populates="producer_invocation")  # Relationship to the LStr results of the invocation
    

    consumed_by: List["Invocation"] = Relationship(
        back_populates="consumes", link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
        ),
    )  # Relationship to the invocations that consumed this invocation

    consumes: List["Invocation"] = Relationship(
        back_populates="consumed_by", link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
        ),
    )




class SerializedLStr(SQLModel, table=True):
    """
    Represents a Language String (LStr) result from an LMP invocation.
    
    This class is used to store the output of LMP invocations.
    """
    id: Optional[int] = Field(default=None, primary_key=True)  # Unique identifier for the LStr
    content: str  # The actual content of the LStr
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))  # Logits associated with the LStr, if available
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id", index=True)  # ID of the Invocation that produced this LStr
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")  # Relationship to the Invocation that produced this LStr

    # Convert an SerializedLStr to an lstr
    def deserialize(self) -> lstr:
        return lstr(self.content, logits=self.logits, _origin_trace=frozenset([self.producer_invocation_id]))
