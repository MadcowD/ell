import os
import subprocess
import shutil
import sys
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

class NPMInstall(object):
    def run_npm_install(self):
        print("Running npm install")
        if sys.platform == "win32":
            subprocess.check_call('npm install', cwd='ell-studio', shell=True)
        else:
            subprocess.check_call(['npm', 'install'], cwd='ell-studio')

class NPMBuild(object):
    def run_npm_build(self):
        print("Running npm build")
        if sys.platform == "win32":
            subprocess.check_call('npm run build', cwd='ell-studio', shell=True)
        else:
            subprocess.check_call(['npm', 'run', 'build'], cwd='ell-studio')

    def copy_static_files(self):
        source_dir = os.path.join('ell-studio', 'build')
        target_dir = os.path.join('src', 'ell', 'studio', 'static')
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)
        print(f"Copied static files from {source_dir} to {target_dir}")

class CustomDevelop(develop, NPMInstall):
    def run(self):
        self.run_npm_install()
        develop.run(self)

class CustomInstall(install, NPMBuild):
    def run(self):
        self.run_npm_build()
        self.copy_static_files()
        install.run(self)

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def read_requirements():
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ell",
    version="0.0.1",
    author="William Guss",
    author_email="will@lrsys.xyz",
    description="ell - a functional language model programming framework",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/MadcowD/ell-studio",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        'ell.studio': ['static/*', 'static/**/*'],
    },
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "ell-studio=ell.studio.__main__:main",
        ],
    },
    cmdclass={
        'develop': CustomDevelop,
        'install': CustomInstall,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)