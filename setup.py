#!/usr/bin/env python3
"""
Setup script for SysAgent CLI.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements from pyproject.toml
def get_requirements():
    """Extract requirements from pyproject.toml."""
    import tomllib
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    
    return data.get("project", {}).get("dependencies", [])

setup(
    name="sysagent-cli",
    version="0.1.0",
    description="Secure, intelligent command-line assistant for OS automation and control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SysAgent Team",
    author_email="team@sysagent.dev",
    url="https://github.com/sysagent/sysagent-cli",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "sysagent=sysagent.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    keywords="cli automation llm system assistant",
    project_urls={
        "Homepage": "https://github.com/sysagent/sysagent-cli",
        "Documentation": "https://sysagent-cli.readthedocs.io",
        "Repository": "https://github.com/sysagent/sysagent-cli",
        "Bug Tracker": "https://github.com/sysagent/sysagent-cli/issues",
    },
) 