import os
import subprocess
import shutil


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



def main():
    npm_install()
    npm_build()


if __name__ == "__main__":
    main()
