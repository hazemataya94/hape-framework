from dataclasses import dataclass, field


@dataclass
class DetectedProject:
    framework: str
    build_flavor: str
    app_name: str
    project_path: str
    build_output_dir: str


@dataclass
class InitCicdResult:
    project_path: str
    deployment_type: str
    framework: str
    build_flavor: str
    created_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FileWriteResult:
    created_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)


if __name__ == "__main__":
    print(InitCicdResult(project_path="/path/to/project", deployment_type="kubernetes", framework="reactjs", build_flavor="vite"))
