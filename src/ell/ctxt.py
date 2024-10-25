from contextvars import ContextVar
from uuid import uuid4

session_id_context: ContextVar[str] = ContextVar('session_id', default='')

def get_session_id() -> str:
    """Get current session ID or create new one"""
    session_id = session_id_context.get()
    if not session_id:
        session_id = str(uuid4())
        session_id_context.set(session_id)
    
    return session_id

def set_session_id(session_id: str) -> None:
    """Set session ID in current context"""
    session_id_context.set(session_id)