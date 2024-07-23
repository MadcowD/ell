# Let's define the core types.
from dataclasses import dataclass
from typing import Callable, Dict, List, Union

from typing import Any
from ell.lstr import lstr
from ell.util.dict_sync_meta import DictSyncMeta

from datetime import datetime
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


class SerializedLMPUses(SQLModel, table=True):
    """
    Represents the many-to-many relationship between SerializedLMPs.
    
    This class is used to track which LMPs use or are used by other LMPs.
    """

    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True)  # ID of the LMP that is being used
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True)  # ID of the LMP that is using the other LMP



class SerializedLMP(SQLModel, table=True):
    """
    Represents a serialized Language Model Program (LMP).
    
    This class is used to store and retrieve LMP information in the database.
    """
    lmp_id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the LMP, now an index
    name: str  # Name of the LMP
    source: str  # Source code or reference for the LMP
    dependencies: str  # List of dependencies for the LMP, stored as a string
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Timestamp of when the LMP was created
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

class LStrOriginator(SQLModel, table=True):
    """
    Represents the many-to-many relationship between LStrs and their originating SerializedLMPs.
    
    This class is used to track which LMPs originated which LStrs.
    """
    id: Optional[int] = Field(default=None, primary_key=True)  # Unique identifier for the relationship
    lstr_id: int = Field(foreign_key="serializedlstr.id")  # ID of the LStr
    invocation_id: int = Field(foreign_key="invocation.id")  # ID of the originating LMP



class InvocationConsumes(SQLModel, table=True):
    """
    Represents a many-to-many relationship between Invocations and other Invocations (it's a 1st degree link in the trace graph)

    This class is used to keep track of when an invocation consumes a in its kwargs or args a result of another invocation.
    """
    invocaton_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True)  # ID of the Invocation that is consuming another Invocation
    invocaton_consumed_id: str = Field(foreign_key="invocation.id", primary_key=True)  # ID of the Invocation that is being consumed by another Invocation

class Invocation(SQLModel, table=True):
    """
    Represents an invocation of an LMP.
    
    This class is used to store information about each time an LMP is called.
    """
    id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the invocation
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id")  # ID of the LMP that was invoked
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))  # Arguments used in the invocation
    kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))  # Keyword arguments used in the invocation
    
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Timestamp of when the invocation was created
    invocation_kwargs: str  # Additional keyword arguments for the invocation

    # Relationships
    lmp: SerializedLMP = Relationship(back_populates="invocations")  # Relationship to the LMP that was invoked
    results: List[SerializedLStr] = Relationship(back_populates="producer_invocation")  # Relationship to the LStr results of the invocation


    # Consumes
    consumed_by: Optional[List["Invocation"]] = Relationship(
        back_populates="consumes",
        link_model=InvocationConsumes,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationConsumes.invocaton_consumer_id",
            secondaryjoin="Invocation.id==InvocationConsumes.invocaton_consumed_id",
        ),
    )
    consumes: List["Invocation"]  = Relationship(
        back_populates="consumed_by",
        link_model=InvocationConsumes,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationConsumes.invocaton_consumed_id",
            secondaryjoin="Invocation.id==InvocationConsumes.invocaton_consumer_id",
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
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id")  # ID of the Invocation that produced this LStr

    originator: List[SerializedLMP] = Relationship(back_populates="results", link_model=LStrOriginator)  # Relationship to the LMP(s) that originated this LStr
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")  # Relationship to the Invocation that produced this LStr


lmp() <- result_lstrs[]  ...compute... another_lmp(result_lstrs[]) <- new_result[]

invocation -> lstrs <- another_invoke
                |
                |
         third invocation    (trace(3rd invocation) = [invocation, another_invocation]
                              

orignators in ell will always be invocation ids.

when i get a new lstr from calling an LMP, i will get the id of the invocaiton that produced it as the sole originator


some_lmp() -> y:= lstr("content", originator=invocation_id of that call.)

y += x 

some_lmp() -> y:= lstr("content", originator=(invocation_id), instantenous_meta_data={
      logits, 
      completion id
      model id
      invocation_id,
      lmp_id.
})



y.invocation_id


y += " 123"
y = some_lmp(meta_data = True)




