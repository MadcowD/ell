#%%
from typing import Any, FrozenSet, Optional, Type, TypeVar, Union
from abc import ABC, abstractmethod

T = TypeVar('T')

class OriginTracedMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict):
        # Add origin tracing properties and methods
        attrs['__origin_trace__'] = frozenset()
        
        def __init__(self, value: Any, origin_trace: Optional[Union[str, FrozenSet[str]]] = None):
            super(self.__class__, self).__init__(value)
            if isinstance(origin_trace, str):
                self.__origin_trace__ = frozenset({origin_trace})
            else:
                self.__origin_trace__ = frozenset(origin_trace) if origin_trace is not None else frozenset()

        attrs['__init__'] = __init__

        @property
        def _origin_trace(self) -> FrozenSet[str]:
            return self.__origin_trace__

        attrs['_origin_trace'] = _origin_trace

        # Create the class
        return super().__new__(cls, name, bases, attrs)

class OriginTraced(metaclass=OriginTracedMeta):
    def __init__(self, value: Any, origin_trace: Optional[Union[str, FrozenSet[str]]] = None):
        pass

    def _combine_origin_traces(self, other: 'OriginTraced') -> FrozenSet[str]:
        return self._origin_trace.union(other._origin_trace)

def origin_traced(base_class: Type[T]) -> Type[T]:
    class WrappedClass(base_class, OriginTraced):
        def __init__(self, value: Any, origin_trace: Optional[Union[str, FrozenSet[str]]] = None):
            base_class.__init__(self, value)
            OriginTraced.__init__(self, value, origin_trace)

        def _combine_origin_traces(self, other: 'OriginTraced') -> FrozenSet[str]:
            return self._origin_trace.union(other._origin_trace if isinstance(other, OriginTraced) else frozenset())

        def __repr__(self):
            return f"{self.__class__.__name__}({base_class.__repr__(self)}, origin_trace={self._origin_trace})"

    return WrappedClass

# Create origin-traced versions of built-in types
lstr = origin_traced(str)
lint = origin_traced(int)
lbool = origin_traced(bool)


#%%
x = lstr("hello", origin_trace="hello")