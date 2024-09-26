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
    print(f"Checking if module '{module_name}' should be imported")
    if module_name.startswith("ell"):
        print(f"Module '{module_name}' starts with 'ell', returning True")
        return True
    try:
        try:
            print(f"Attempting to find spec for module '{module_name}'")
            spec = importlib.util.find_spec(module_name)
            print(f"Spec for module '{module_name}': {spec}")
        except ValueError as e:
            print(f"ValueError occurred while finding spec for '{module_name}': {e}")
            return False
        if spec is None:
            print(f"Spec for module '{module_name}' is None, returning False")
            return False

        origin = spec.origin
        print(f"Origin for module '{module_name}': {origin}")
        if origin is None:
            print(f"Origin for module '{module_name}' is None, returning False")
            return False
        if spec.has_location:
            print(f"Module '{module_name}' has location")
            origin_path = Path(origin).resolve()
            print(f"Resolved origin path: {origin_path}")
            
            site_packages = list(site.getsitepackages()) + (list(site.getusersitepackages()) if isinstance(site.getusersitepackages(), list) else [site.getusersitepackages()])
            print(f"Site packages: {site_packages}")

            additional_paths = [Path(p).resolve() for p in sys.path if Path(p).resolve() not in map(Path, site_packages)]
            print(f"Additional paths: {additional_paths}")

            project_root = Path(os.environ.get("ELL_PROJECT_ROOT", os.getcwd())).resolve()
            print(f"Project root: {project_root}")

            site_packages_paths = [Path(p).resolve() for p in site_packages]
            stdlib_path = sysconfig.get_paths().get("stdlib")
            if stdlib_path:
                site_packages_paths.append(Path(stdlib_path).resolve())
            print(f"Site packages paths (including stdlib): {site_packages_paths}")
            
            additional_paths = [Path(p).resolve() for p in additional_paths]
            local_paths = [project_root]
            print(f"Local paths: {local_paths}")
            
            cwd = Path.cwd().resolve()
            additional_paths = [path for path in additional_paths if path != cwd]
            print(f"Additional paths (excluding cwd): {additional_paths}")

            for pkg in site_packages_paths:
                if origin_path.is_relative_to(pkg):
                    print(f"Module '{module_name}' is relative to site package {pkg}, returning True")
                    return True

            for path in additional_paths:
                if origin_path.is_relative_to(path):
                    print(f"Module '{module_name}' is relative to additional path {path}, returning False")
                    return False

            for local in local_paths:
                if origin_path.is_relative_to(local):
                    print(f"Module '{module_name}' is relative to local path {local}, returning False")
                    return False

            print(f"Module '{module_name}' doesn't match any criteria, returning True")
        return True

    except Exception as e:
        print(f"Failed to find spec for {module_name}. Please report to https://github.com/MadcowD/ell/issues. Error: {e}")
        if raise_on_error:
            raise e
        # raise e
        return True