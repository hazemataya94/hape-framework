from pathlib import Path

from setuptools import find_packages, setup


def _read_version() -> str:
    return Path(__file__).with_name("VERSION").read_text(encoding="utf-8").strip()


def _read_requirements() -> list[str]:
    requirements_path = Path(__file__).with_name("requirements.txt")
    requirements = []
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


setup(
    name="hape",
    version=_read_version(),
    description="HAPE Automation: CLI for Platform and DevOps automations.",
    long_description=Path(__file__).with_name("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    license="MIT",
    author="Hazem Ataya",
    url="https://github.com/hazemataya94/hape-framework",
    project_urls={
        "Documentation": "https://framework.hapesolutions.com",
        "Source": "https://github.com/hazemataya94/hape-framework",
        "Issues": "https://github.com/hazemataya94/hape-framework/issues",
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=_read_requirements(),
    entry_points={"console_scripts": ["hape=cli.main:main"]},
    python_requires=">=3.9",
)
