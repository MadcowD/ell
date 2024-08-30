ell.types
=========

.. automodule:: ell.types
   :members:
   :undoc-members:
   :show-inheritance:

Submodules
----------

ell.types.lmp
-------------

.. automodule:: ell.types.lmp
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.SerializedLMPUses
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.SerializedLMPBase
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.SerializedLMP
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.InvocationTrace
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.InvocationBase
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.InvocationContentsBase
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.InvocationContents
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.lmp.Invocation
   :members:
   :undoc-members:
   :show-inheritance:

ell.types.message
-----------------

.. automodule:: ell.types.message
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.message.ToolResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.message.ToolCall
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.message.ContentBlock
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ell.types.message.Message
   :members:
   :undoc-members:
   :show-inheritance:

.. autofunction:: ell.types.message.system

.. autofunction:: ell.types.message.user

.. autofunction:: ell.types.message.assistant

.. autofunction:: ell.types.message.coerce_content_list

Type Aliases
------------

.. py:data:: ell.types.message.InvocableTool
   :annotation: = Callable[..., Union[ToolResult, _lstr_generic, List[ContentBlock]]]

.. py:data:: ell.types.message.LMPParams
   :annotation: = Dict[str, Any]

.. py:data:: ell.types.message.MessageOrDict
   :annotation: = Union[Message, Dict[str, str]]

.. py:data:: ell.types.message.Chat
   :annotation: = List[Message]

.. py:data:: ell.types.message.MultiTurnLMP
   :annotation: = Callable[..., Chat]

.. py:data:: ell.types.message.OneTurn
   :annotation: = Callable[..., _lstr_generic]

.. py:data:: ell.types.message.ChatLMP
   :annotation: = Callable[[Chat, Any], Chat]

.. py:data:: ell.types.message.LMP
   :annotation: = Union[OneTurn, MultiTurnLMP, ChatLMP]

.. py:data:: ell.types.message.InvocableLM
   :annotation: = Callable[..., _lstr_generic]