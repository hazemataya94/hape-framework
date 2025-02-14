from setuptools import setup, find_packages

setup(
    name="hape",
    version="0.2.64",
    packages=["hape"],
    include_package_data=True,
    install_requires=[
        "python-dotenv==1.0.1"
    ],
    entry_points={
        "console_scripts": [
            "hape=hape.hape_cli.cli:main",
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
