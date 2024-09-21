import os
import subprocess
import shutil
import toml


def run_command(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command {command} failed with return code {result.returncode}"
        )


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


def get_ell_version():
    pyproject_path = "pyproject.toml"
    pyproject_data = toml.load(pyproject_path)
    return pyproject_data["tool"]["poetry"]["version"]


def main():
    ell_version = get_ell_version()
    os.environ['REACT_APP_ELL_VERSION'] = ell_version
    npm_install()
    npm_build()


if __name__ == "__main__":
    main()
