#!/usr/bin/env python3

from setuptools import setup


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
        "palamedes_client",
        "palamedes_server",
        "palamedes_store",
    ],
    packages=["palamedes_sdk"],
)
