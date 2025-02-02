from setuptools import setup, find_packages

setup(
    name="appname",
    version="0.1.32",
    packages=find_packages(include=["appname", "appname.*"]),
    install_requires=[
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "appname=appname.cli:main",
        ],
    },
    author="Hazem Ataya",
    author_email="hazem.ataya94@gmail.com",
    description="HAPE Framework: Build an Automation Tool With Ease",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://pypi_link",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
