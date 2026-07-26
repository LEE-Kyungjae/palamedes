#!/usr/bin/env python3

from setuptools import find_packages, setup


AGENTS_SRC = "scaffolds/palamedes_agents/src"


setup(
    name="palamedes",
    version="0.5.0",
    description="A local, agent-friendly planning kernel with a thin Python SDK surface.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="LEE Kyungjae",
    license="MIT",
    python_requires=">=3.9",
    py_modules=[
        "palamedes",
        "palamedes_agent",
        "palamedes_chat",
        "palamedes_client",
        "palamedes_mission",
        "palamedes_observe",
        "palamedes_proof",
        "palamedes_watch",
        "palamedes_server",
        "palamedes_store",
    ],
    packages=["palamedes_sdk", *find_packages(where=AGENTS_SRC)],
    package_dir={"palamedes_agents": f"{AGENTS_SRC}/palamedes_agents"},
    package_data={
        "palamedes_agents": [
            "contracts/*.json",
            "schemas/*.json",
            "skills/*.json",
            "skills/manifests/*.json",
            "prompts/*.md",
        ]
    },
    entry_points={"console_scripts": ["palamedes=palamedes:main"]},
)
