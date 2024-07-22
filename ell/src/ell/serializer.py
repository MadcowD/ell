from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List

class Serializer(ABC):
    @abstractmethod
    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], 
                  created_at: float, is_lmp: bool, lm_kwargs: Optional[str], 
                  uses: Dict[str, Any]) -> Optional[Any]:
        pass

    @abstractmethod
    def write_invocation(self, lmp_id: str, args: str, kwargs: str, result: str, 
                         created_at: float, invocation_kwargs: Dict[str, Any]) -> Optional[Any]:
        pass

    @abstractmethod
    def get_lmps(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def search_lmps(self, query: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def search_invocations(self, query: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_lmp_versions(self, lmp_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        pass