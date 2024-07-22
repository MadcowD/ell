import os
import json
from typing import Any, Optional, Dict, List
import ell.serializer
import numpy as np
import glob
from operator import itemgetter

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return obj.to_json()
        if isinstance(obj, str):
            return obj
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        try:
            return super().default(obj)
        except TypeError as e:
            return str(obj)


class FilesystemSerializer(ell.serializer.Serializer):
    def __init__(self, storage_dir: str, max_file_size: int = 1024 * 1024):  # 1MB default
        self.storage_dir = storage_dir
        self.max_file_size = max_file_size
        os.makedirs(storage_dir, exist_ok=True)
        self.open_files = {}

    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], 
                  created_at: float, is_lmp: bool, lm_kwargs: Optional[str], 
                  uses: Dict[str, Any]) -> Optional[Any]:
        """
        Write the LMP (Language Model Program) to a JSON file.
        """
        file_path = os.path.join(self.storage_dir, 'programs', f"{name}_{lmp_id}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        lmp_data = {
            'lmp_id': lmp_id,
            'name': name,
            'source': source,
            'dependencies': dependencies,
            'created_at': created_at,
            'is_lmp': is_lmp,
            'lm_kwargs': lm_kwargs,
            'uses': uses
        }

        with open(file_path, 'w') as f:
            json.dump(lmp_data, f, cls=CustomJSONEncoder)

        return None

    def write_invocation(self, lmp_id: str, args: str, kwargs: str, result: str, 
                         created_at: float, invocation_kwargs: Dict[str, Any]) -> Optional[Any]:
        """
        Write an LMP invocation to a JSONL file in a nested folder structure.
        """
        dir_path = os.path.join(self.storage_dir, 'invocations', lmp_id[:2], lmp_id[2:4], lmp_id[4:])
        os.makedirs(dir_path, exist_ok=True)

        if lmp_id not in self.open_files:
            index = 0
            while True:
                file_path = os.path.join(dir_path, f"invocations.{index}.jsonl")
                if not os.path.exists(file_path) or os.path.getsize(file_path) < self.max_file_size:
                    self.open_files[lmp_id] = {'file': open(file_path, 'a'), 'path': file_path}
                    break
                index += 1

        invocation_data = {
            'lmp_id': lmp_id,
            'args': args,
            'kwargs': kwargs,
            'result': result,
            'invocation_kwargs': invocation_kwargs,
            'created_at': created_at
        }

        file_info = self.open_files[lmp_id]
        file_info['file'].write(json.dumps(invocation_data, cls=CustomJSONEncoder) + '\n')
        file_info['file'].flush()

        if os.path.getsize(file_info['path']) >= self.max_file_size:
            file_info['file'].close()
            del self.open_files[lmp_id]
        
        return invocation_data

    def get_lmps(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        lmps = []
        for file_path in glob.glob(os.path.join(self.storage_dir, 'programs', '*.json')):
            with open(file_path, 'r') as f:
                lmp = json.load(f)
                if filters:
                    if all(lmp.get(k) == v for k, v in filters.items()):
                        lmps.append(lmp)
                else:
                    lmps.append(lmp)
        return lmps

    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        invocations = []
        dir_path = os.path.join(self.storage_dir, 'invocations', lmp_id[:2], lmp_id[2:4], lmp_id[4:])
        for file_path in glob.glob(os.path.join(dir_path, 'invocations.*.jsonl')):
            with open(file_path, 'r') as f:
                for line in f:
                    invocation = json.loads(line)
                    if filters:
                        if all(invocation.get(k) == v for k, v in filters.items()):
                            invocations.append(invocation)
                    else:
                        invocations.append(invocation)
        return invocations

    def get_lmp(self, lmp_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific LMP by its ID.
        """
        for file_path in glob.glob(os.path.join(self.storage_dir, 'programs', '*.json')):
            with open(file_path, 'r') as f:
                lmp = json.load(f)
                if lmp.get('lmp_id') == lmp_id:
                    return lmp
        return None

    def search_lmps(self, query: str) -> List[Dict[str, Any]]:
        lmps = []
        for file_path in glob.glob(os.path.join(self.storage_dir, 'programs', '*.json')):
            with open(file_path, 'r') as f:
                lmp = json.load(f)
                if query.lower() in json.dumps(lmp).lower():
                    lmps.append(lmp)
        return lmps

    def search_invocations(self, query: str) -> List[Dict[str, Any]]:
        invocations = []
        for dir_path in glob.glob(os.path.join(self.storage_dir, 'invocations', '*', '*', '*')):
            for file_path in glob.glob(os.path.join(dir_path, 'invocations.*.jsonl')):
                with open(file_path, 'r') as f:
                    for line in f:
                        invocation = json.loads(line)
                        if query.lower() in json.dumps(invocation).lower():
                            invocations.append(invocation)
        return invocations

    def get_lmp_versions(self, lmp_id: str) -> List[Dict[str, Any]]:
        """
        Get all versions of an LMP with the given lmp_id.
        """
        target_lmp = self.get_lmp(lmp_id)
        if not target_lmp:
            return []

        versions = []
        for file_path in glob.glob(os.path.join(self.storage_dir, 'programs', f"{target_lmp['name']}_*.json")):
            with open(file_path, 'r') as f:
                lmp = json.load(f)
                versions.append(lmp)

        # Sort versions by created_at timestamp, newest first
        return sorted(versions, key=lambda x: x['created_at'], reverse=True)

    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        """
        Get the latest version of each unique LMP.
        """
        lmps_by_name = {}
        for file_path in glob.glob(os.path.join(self.storage_dir, 'programs', '*.json')):
            with open(file_path, 'r') as f:
                lmp = json.load(f)
                name = lmp['name']
                if name not in lmps_by_name or lmp['created_at'] > lmps_by_name[name]['created_at']:
                    lmps_by_name[name] = lmp

        # Return the list of latest LMPs, sorted by name
        return sorted(lmps_by_name.values(), key=itemgetter('name'))

    def __del__(self):
        """
        Close all open files when the serializer is destroyed.
        """
        for file_info in self.open_files.values():
            file_info['file'].close()

    def install(self):
        """
        Install the serializer into all invocations of the ell wrapper.
        """
        ell.config.register_serializer(self)