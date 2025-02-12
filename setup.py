from setuptools import setup, find_packages

setup(
    name="hape",
    version="0.2.56",
    packages=find_packages(include=["hape", "hape/*"]),
    package_data={},
    include_package_data=True,
    install_requires=[
        "alembic==1.14.1", "cachetools==5.5.1", "certifi==2025.1.31", "charset-normalizer==3.4.1",
        "durationpy==0.9", "google-auth==2.38.0", "greenlet==3.1.1", "idna==3.10", "kubernetes==31.0.0",
        "Mako==1.3.9", "MarkupSafe==3.0.2", "mysql==0.0.3", "mysql-connector-python==9.2.0",
        "mysqlclient==2.2.7", "oauthlib==3.2.2", "pyasn1==0.6.1", "pyasn1_modules==0.4.1",
        "python-dateutil==2.9.0.post0", "python-dotenv==1.0.1", "python-gitlab==5.6.0",
        "python-json-logger==3.2.1", "PyYAML==6.0.2", "requests==2.32.3", "requests-oauthlib==2.0.0",
        "requests-toolbelt==1.0.0", "rsa==4.9", "ruamel.yaml==0.18.10", "ruamel.yaml.clib==0.2.12",
        "six==1.17.0", "SQLAlchemy==2.0.37", "typing_extensions==4.12.2", "urllib3==2.3.0",
        "websocket-client==1.8.0", "PyMySQL==1.1.1"
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
