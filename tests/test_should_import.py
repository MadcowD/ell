import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sysconfig
import sys
import os

# Import the function to be tested
from src.ell.util.should_import import should_import

@pytest.fixture
def mock_project_root(monkeypatch):
    """
    Fixture to mock the ELL_PROJECT_ROOT environment variable.
    """
    project_root = Path("/mock/project/root").resolve()
    monkeypatch.setenv("ELL_PROJECT_ROOT", str(project_root))
    return project_root

@pytest.fixture
def mock_sysconfig_paths():
    """
    Fixture to mock sysconfig.get_paths().
    """
    return {
        "stdlib": "/mock/python/lib",
        "purelib": "/mock/python/lib/site-packages",
        "platlib": "/mock/python/lib/site-packages",
    }

@pytest.fixture
def mock_site_packages():
    """
    Fixture to mock site.getsitepackages() and site.getusersitepackages().
    """
    return ["/mock/python/lib/site-packages", "/mock/user/site-packages"]

def mock_find_spec(module_name, raise_value):
    """
    Helper function to create a mock spec object.
    """
    mock_spec = MagicMock()
    mock_spec.origin = raise_value["origin"]
    mock_spec.has_location = raise_value["has_location"]
    return mock_spec
@pytest.mark.parametrize(
    "module_name, spec_origin, spec_has_location, expected",
    [
        # Third-party module located in site-packages
        (
            "numpy",
            "/mock/python/lib/site-packages/numpy/__init__.py",
            True,
            True,
        ),
        # Standard library module
        (
            "os",
            "/mock/python/lib/os.py",
            True,
            True,
        ),
        # Local module within project root
        (
            "local_module",
            "/mock/project/root/ell/util/local_module.py",
            True,
            False,
        ),
        # Module installed from source in additional paths
        (
            "some_module",
            "/mock/other/path/some_module/__init__.py",
            True,
            False,
        ),
        # Built-in module with no origin
        (
            "sys",
            None,
            False,
            False,
        ),
        # Non-existent module
        (
            "nonexistent_module",
            None,
            False,
            False,
        ),
    ],
)
def test_should_import(
    module_name,
    spec_origin,
    spec_has_location,
    expected,
    mock_project_root,
    mock_sysconfig_paths,
    mock_site_packages,
    monkeypatch,
):
    additional_paths = ["/mock/other/path"]
    with patch("importlib.util.find_spec") as mock_find_spec_func, \
         patch("site.getsitepackages", return_value=mock_site_packages), \
         patch("site.getusersitepackages", return_value=mock_site_packages[-1:]), \
         patch("sysconfig.get_paths", return_value=mock_sysconfig_paths), \
         patch("os.environ.get", return_value=str(mock_project_root)), \
         patch("sys.path", additional_paths + sys.path):

        if spec_origin is not None:
            mock_spec = MagicMock()
            mock_spec.origin = spec_origin
            mock_spec.has_location = spec_has_location
            mock_find_spec_func.return_value = mock_spec
        else:
            mock_find_spec_func.return_value = None

        result = should_import(module_name)
        assert result == expected, f"Failed for module: {module_name}"

def test_should_import_exception_handling(mock_project_root, mock_sysconfig_paths, mock_site_packages, monkeypatch, capsys):
    """
    Test the function's behavior when importlib.util.find_spec raises an exception.
    """
    with patch("importlib.util.find_spec", side_effect=Exception("Test Exception")), \
         patch("site.getsitepackages", return_value=mock_site_packages), \
         patch("site.getusersitepackages", return_value=mock_site_packages[-1:]), \
         patch("sysconfig.get_paths", return_value=mock_sysconfig_paths), \
         patch("os.environ.get", return_value=str(mock_project_root)):

        with pytest.raises(Exception) as exc_info:
            should_import("any_module", raise_on_error=True)
        assert "Test Exception" in str(exc_info.value)

        assert should_import("any_module") == True, "Function should return True when an exception occurs and raise_on_error is False"

def test_should_import_raise_on_error(mock_project_root, mock_sysconfig_paths, mock_site_packages, monkeypatch):
    """
    Test the function's behavior when raise_on_error is True and an exception is raised.
    """
    with patch("importlib.util.find_spec", side_effect=Exception("Test Exception")), \
         patch("site.getsitepackages", return_value=mock_site_packages), \
         patch("site.getusersitepackages", return_value=mock_site_packages[-1:]), \
         patch("sysconfig.get_paths", return_value=mock_sysconfig_paths), \
         patch("os.environ.get", return_value=str(mock_project_root)):

        with pytest.raises(Exception) as exc_info:
            should_import("any_module", raise_on_error=True)
        assert "Test Exception" in str(exc_info.value)

@pytest.mark.parametrize(
    "module_name, spec_origin, spec_has_location, expected",
    [
        # Module in additional_paths (installed from source)
        (
            "source_module",
            "/mock/source/install/source_module/__init__.py",
            True,
            False,
        ),
        # Module in a non-site-packages additional path
        (
            "another_source",
            "/mock/another/path/another_source/__init__.py",
            True,
            False,
        ),
    ],
)
def test_should_import_additional_paths(
    module_name,
    spec_origin,
    spec_has_location,
    expected,
    mock_project_root,
    mock_sysconfig_paths,
    mock_site_packages,
    monkeypatch,
):
    additional_paths = [
        Path("/mock/source/install").resolve(),
        Path("/mock/another/path").resolve(),
    ]

    with patch("importlib.util.find_spec") as mock_find_spec_func, \
         patch("site.getsitepackages", return_value=mock_site_packages), \
         patch("site.getusersitepackages", return_value=mock_site_packages[-1:]), \
         patch("sysconfig.get_paths", return_value=mock_sysconfig_paths), \
         patch("os.environ.get", return_value=str(mock_project_root)), \
         patch("sys.path", new=[str(p) for p in additional_paths] + sys.path):

        if spec_origin is not None:
            mock_spec = MagicMock()
            mock_spec.origin = spec_origin
            mock_spec.has_location = spec_has_location
            mock_find_spec_func.return_value = mock_spec
        else:
            mock_find_spec_func.return_value = None

        result = should_import(module_name)
        assert result == expected, f"Failed for module: {module_name}"

@pytest.mark.parametrize(
    "module_name, spec_origin, spec_has_location, expected",
    [
        # Local module with ELL prefix
        (
            "ell.local_module",
            "/mock/project/root/ell/local_module.py",
            True,
            True,
        ),
        # Third-party module with similar name but inside site-packages
        (
            "ell_thirdparty",
            "/mock/python/lib/site-packages/ell_thirdparty/__init__.py",
            True,
            True,
        ),
    ],
)
def test_should_import_ell_prefix(
    module_name,
    spec_origin,
    spec_has_location,
    expected,
    mock_project_root,
    mock_sysconfig_paths,
    mock_site_packages,
    monkeypatch,
):
    with patch("importlib.util.find_spec") as mock_find_spec_func, \
         patch("site.getsitepackages", return_value=mock_site_packages), \
         patch("site.getusersitepackages", return_value=mock_site_packages[-1:]), \
         patch("sysconfig.get_paths", return_value=mock_sysconfig_paths), \
         patch("os.environ.get", return_value=str(mock_project_root)):

        if spec_origin is not None:
            mock_spec = MagicMock()
            mock_spec.origin = spec_origin
            mock_spec.has_location = spec_has_location
            mock_find_spec_func.return_value = mock_spec
        else:
            mock_find_spec_func.return_value = None

        result = should_import(module_name)
        assert result == expected, f"Failed for module: {module_name}"

def test_should_import_without_origin(mock_project_root, mock_sysconfig_paths, mock_site_packages, monkeypatch):
    """
    Test behavior when the module spec exists but has no origin.
    Typically for built-in modules.
    """
    with patch("importlib.util.find_spec") as mock_find_spec_func, \
         patch("site.getsitepackages", return_value=mock_site_packages), \
         patch("site.getusersitepackages", return_value=mock_site_packages[-1:]), \
         patch("sysconfig.get_paths", return_value=mock_sysconfig_paths), \
         patch("os.environ.get", return_value=str(mock_project_root)):

        mock_spec = MagicMock()
        mock_spec.origin = None
        mock_spec.has_location = False
        mock_find_spec_func.return_value = mock_spec

        result = should_import("built_in_module")
        assert result == False, "Built-in modules should not be imported"

def test_should_import_with_no_spec(mock_project_root, mock_sysconfig_paths, mock_site_packages, monkeypatch):
    """
    Test behavior when find_spec returns None, indicating the module cannot be found.
    """
    with patch("importlib.util.find_spec", return_value=None), \
         patch("site.getsitepackages", return_value=mock_site_packages), \
         patch("site.getusersitepackages", return_value=mock_site_packages[-1:]), \
         patch("sysconfig.get_paths", return_value=mock_sysconfig_paths), \
         patch("os.environ.get", return_value=str(mock_project_root)):

        result = should_import("unknown_module")
        assert result == False, "Unknown modules should not be imported"


def test_should_import_standard_library():
    """
    Test importing a standard library module without mocking.
    """
    import importlib

    module_name = "json"
    result = should_import(module_name)
    assert result == True, f"Failed to import standard library module: {module_name}"


@pytest.mark.skipif(
    "requests" not in sys.modules and not importlib.util.find_spec("requests"),
    reason="requests module is not installed",
)
def test_should_import_third_party():
    """
    Test importing a third-party module without mocking.
    Ensures that the module is installed in the environment.
    """
    import importlib

    module_name = "requests"
    result = should_import(module_name)
    assert result == True, f"Failed to import third-party module: {module_name}"


def test_should_import_local_module():
    """
    Test importing a local module within the project without mocking.
    Assumes that 'src.ell.util.local_module' exists.
    """
    module_name = "src.ell.util.local_module"
    result = should_import(module_name)
    assert result == False, f"Local module should not be imported: {module_name}"


def test_should_import_nonexistent_module():
    """
    Test importing a non-existent module without mocking.
    """
    module_name = "this_module_does_not_exist"
    result = should_import(module_name)
    assert result == False, f"Non-existent module should not be imported: {module_name}"


@pytest.mark.parametrize(
    "module_name, expected",
    [
        ("os", True),  # Standard library module
        ("sys", True),  # Standard library module
    ],
)
def test_should_import_multiple_standard_library_modules(module_name, expected):
    """
    Test importing multiple standard library modules without mocking.
    """
    result = should_import(module_name)
    assert result == expected, f"Failed to import standard library module: {module_name}"


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Test specific to Windows operating systems",
)
def test_should_import_windows_specific_module():
    """
    Test importing a Windows-specific module without mocking.
    """
    module_name = "msvcrt"  # Windows-specific module
    result = should_import(module_name)
    assert result == True, f"Failed to import Windows-specific module: {module_name}"


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Test specific to Unix-like operating systems",
)
def test_should_import_unix_specific_module():
    """
    Test importing a Unix-specific module without mocking.
    """
    module_name = "pwd"  # Unix-specific module
    result = should_import(module_name)
    assert result == True, f"Failed to import Unix-specific module: {module_name}"