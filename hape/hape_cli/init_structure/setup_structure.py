SETUP_PY = """
from setuptools import setup, find_packages

setup(
    name="{{project_name}}",
    version="0.0.1",
    packages=find_packages(include=["{{project_name}}", "{{project_name}}/*"]),
    package_data={},
    include_package_data=True,
    install_requires=[
        
    ],
    entry_points={
        "console_scripts": [
            "{{project_name}}={{project_name}}.{{project_name}}_cli.cli:main",
        ],
    },
    author="Hazem Ataya",
    author_email="hazem.ataya94@gmail.com",
    description="HAPE Framework: Build an Automation Tool With Ease",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hazemataya94/hape-framework",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)

""".strip()