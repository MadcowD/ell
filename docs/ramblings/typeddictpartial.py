from typing import TypedDict, Any, Dict, Type, TypeVar

T = TypeVar('T', bound='PartialTypedDict')

class PartialTypedDictMeta(type):
    def __new__(cls, name: str, bases: tuple, namespace: Dict[str, Any], *, partial: bool = False):
        annotations = namespace.get('__annotations__', {})
        if partial:
            namespace['__required_keys__'] = frozenset()
            namespace['__optional_keys__'] = frozenset(annotations.keys())
        else:
            namespace['__required_keys__'] = frozenset(annotations.keys())
            namespace['__optional_keys__'] = frozenset()
        
        return super().__new__(cls, name, bases, namespace)

class PartialTypedDict(Dict[str, Any], metaclass=PartialTypedDictMeta):
    def __init_subclass__(cls, partial: bool = False):
        super().__init_subclass__()
    
    @classmethod
    def __class_getitem__(cls: Type[T], key) -> Type[T]:
        return cls

def create_partial_typed_dict(name: str, fields: Dict[str, Any], *, partial: bool = False) -> Type[PartialTypedDict]:
    return PartialTypedDictMeta(name, (PartialTypedDict,), {'__annotations__': fields}, partial=partial)

# Example usage:
class Movie(PartialTypedDict, partial=True):
    title: str
    year: int

# Or using the factory function:
Person = create_partial_typed_dict('Person', {'name': str, 'age': int}, partial=True)

# Usage
movie: Movie = {'title': 'Inception'}  # Valid, 'year' is optional
person: Person = {'name': 'John'}  # Valid, 'age' is optional
