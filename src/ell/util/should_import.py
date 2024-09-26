import importlib.util
import os
import site
import sys
import sysconfig
from pathlib import Path


def should_import(module_name: str, raise_on_error: bool = False) -> bool:
    """
    Determines whether a module should be imported based on its origin.
    Excludes local modules and standard library modules.

    Args:
        module_name (str): The name of the module to check.

    Returns:
        bool: True if the module should be imported (i.e., it's a third-party module), False otherwise.
    """
    if module_name.startswith("ell"):
        return True
    try:
        try:
            spec = importlib.util.find_spec(module_name)
        except ValueError:
            return False
        if spec is None:
            return False

        origin = spec.origin
        if origin is None:
            return False
        if spec.has_location:
            origin_path = Path(origin).resolve()
            
            site_packages = list(site.getsitepackages()) + (list(site.getusersitepackages()) if isinstance(site.getusersitepackages(), list) else [site.getusersitepackages()])

            additional_paths = [Path(p).resolve() for p in sys.path if Path(p).resolve() not in map(Path, site_packages)]

            project_root = Path(os.environ.get("ELL_PROJECT_ROOT", os.getcwd())).resolve()

            site_packages_paths = [Path(p).resolve() for p in site_packages]
            stdlib_path = sysconfig.get_paths().get("stdlib")
            if stdlib_path:
                site_packages_paths.append(Path(stdlib_path).resolve())
            
            additional_paths = [Path(p).resolve() for p in additional_paths]
            local_paths = [project_root]
            
            cwd = Path.cwd().resolve()
            additional_paths = [path for path in additional_paths if path != cwd]

            for pkg in site_packages_paths:
                if origin_path.is_relative_to(pkg):
                    return True

            for path in additional_paths:
                if origin_path.is_relative_to(path):
                    return False

            for local in local_paths:
                if origin_path.is_relative_to(local):
                    return False

        return True

    except Exception as e:
        if raise_on_error:
            raise e
        return True