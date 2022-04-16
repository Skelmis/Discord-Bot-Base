import re
from setuptools import setup

with open("readme.md", "r") as fh:
    long_description = fh.read()

_version_regex = (
    r"^__version__ = ('|\")((?:[0-9]+\.)*[0-9]+(?:\.?([a-z]+)(?:\.?[0-9])?)?)\1$"
)

try:
    with open("bot_base/__init__.py") as stream:
        match = re.search(_version_regex, stream.read(), re.MULTILINE)
        version = match.group(2)
except FileNotFoundError:
    version = "0.0.0"


def parse_requirements_file(path):
    with open(path) as fp:
        dependencies = (d.strip() for d in fp.read().split("\n") if d.strip())
        return [d for d in dependencies if not d.startswith("#")]


setup(
    name="Bot-Base",
    version=version,
    author="Skelmis",
    author_email="ethan@koldfusion.xyz",
    description="A simplistic yet feature rich discord bot template.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Skelmis/DPY-Bot-Base",
    extras_requires={
        "nextcord": ["nextcord"],
        "disnake": ["disnake"],
    },
    packages=[
        "bot_base",
        "bot_base.db",
        "bot_base.blacklist",
        "bot_base.wraps",
        "bot_base.caches",
        "bot_base.converters",
        "bot_base.cogs",
        "bot_base.paginators",
    ],
    install_requires=parse_requirements_file("requirements.txt"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires=">=3.8",
)
