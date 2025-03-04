from setuptools import setup, find_packages

setup(
    name="hape",
    version="0.2.113",
    packages=["hape"],
    include_package_data=True,
    install_requires=[
        "alembic==1.14.1",
        "build==1.2.2.post1",
        "cachetools==5.5.1",
        "certifi==2024.12.14",
        "cffi==1.17.1",
        "charset-normalizer==3.4.1",
        "cryptography==44.0.0",
        "docutils==0.21.2",
        "durationpy==0.9",
        "google-auth==2.38.0",
        "greenlet==3.1.1",
        "idna==3.10",
        "iniconfig==2.0.0",
        "jaraco.classes==3.4.0",
        "jaraco.context==6.0.1",
        "jaraco.functools==4.1.0",
        "keyring==25.6.0",
        "kubernetes==31.0.0",
        "Mako==1.3.8",
        "markdown-it-py==3.0.0",
        "MarkupSafe==3.0.2",
        "mdurl==0.1.2",
        "more-itertools==10.6.0",
        "mysql==0.0.3",
        "mysql-connector-python==9.2.0",
        "mysqlclient==2.2.7",
        "nh3==0.2.20",
        "oauthlib==3.2.2",
        "packaging==24.2",
        "pkginfo==1.12.0",
        "pluggy==1.5.0",
        "pyasn1==0.6.1",
        "pyasn1_modules==0.4.1",
        "pycparser==2.22",
        "Pygments==2.19.1",
        "PyMySQL==1.1.1",
        "pyproject_hooks==1.2.0",
        "pytest==8.3.4",
        "python-dateutil==2.9.0.post0",
        "python-dotenv==1.0.1",
        "python-gitlab==5.6.0",
        "python-json-logger==3.2.1",
        "PyYAML==6.0.2",
        "readme_renderer==44.0",
        "requests==2.32.3",
        "requests-oauthlib==2.0.0",
        "requests-toolbelt==1.0.0",
        "rfc3986==2.0.0",
        "rich==13.9.4",
        "rsa==4.9",
        "ruamel.yaml==0.18.10",
        "ruamel.yaml.clib==0.2.12",
        "setuptools==75.8.0",
        "six==1.17.0",
        "SQLAlchemy==2.0.37",
        "twine==6.0.1",
        "typing_extensions==4.12.2",
        "urllib3==2.3.0",
        "websocket-client==1.8.0",
        "wheel==0.45.1",
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
