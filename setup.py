import setuptools
import subprocess
import shutil

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

subprocess.call(["pipreqs", ".", "--force"])

setuptools.setup(
    name="dfana",
    version="0.0.1",
    author="mb",
    description="a module for analyzing dataframe contents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mb-89/dfana",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=open("requirements.txt", "r").readlines()
)

shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("src/dfana.egg-info", ignore_errors=True)