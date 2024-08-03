import os
import subprocess
import shutil
import sys
import toml


def run_command(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command {command} failed with return code {result.returncode}"
        )


def sync_version():
    with open("pyproject.toml", "r") as f:
        pyproject = toml.load(f)
    version = pyproject.get("tool", {}).get("poetry", {}).get("version")
    if not version:
        raise ValueError("Version not found in pyproject.toml")
    version = "v" + version
    print(f"setting {version=}")
    run_command(f"git tag -f {version}")


def python_install():
    sync_version()
    run_command("poetry self add poetry-dynamic-versioning")
    run_command("poetry dynamic-versioning enable")
    run_command("pip uninstall -y ell")
    run_command("poetry install")
    run_command("poetry build")
    # Use a wildcard pattern that works on both Windows and Unix-like systems
    dist_dir = "dist"
    dist_files = [
        os.path.join(dist_dir, f) for f in os.listdir(dist_dir) if f.endswith(".whl")
    ]
    if not dist_files:
        raise RuntimeError("No .whl files found in dist directory")
    for file in dist_files:
        run_command(f"pip install {file}")
    shutil.rmtree(dist_dir, ignore_errors=True)


def npm_install():
    print("Running npm install")
    run_command("npm install", cwd="ell-studio")


def npm_build():
    print("Running npm build")
    run_command("npm run build", cwd="ell-studio")
    print("Copying static files")
    source_dir = os.path.join("ell-studio", "build")
    target_dir = os.path.join("src", "ell", "studio", "static")
    shutil.rmtree(target_dir, ignore_errors=True)
    shutil.copytree(source_dir, target_dir)
    print(f"Copied static files from {source_dir} to {target_dir}")


def main():
    npm_install()
    npm_build()
    python_install()


if __name__ == "__main__":
    main()
