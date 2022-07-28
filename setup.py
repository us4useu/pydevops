import setuptools

version_namespace = {}
with open("pydevops/version.py") as f:
    exec(f.read(), version_namespace)


setuptools.setup(
    name="pydevops",
    version=version_namespace["__version__"],
    author="us4us Ltd.",
    author_email="support@us4us.eu",
    description="Python tools for us4us devops",
    long_description="Python tools for us4us devops",
    long_description_content_type="text/markdown",
    url="https://us4us.eu",
    packages=setuptools.find_packages(exclude=[]),
    classifiers=[
        "Development Status :: 1 - Planning",

        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",

        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "pydevops = pydevops:main"
        ]
    }
)