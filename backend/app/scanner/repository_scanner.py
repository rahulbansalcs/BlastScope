from pathlib import Path
from dataclasses import dataclass
from typing import List
@dataclass
class RepositoryInfo:
    path: str
    file_count: int
    python_file_count: int
    total_lines: int
    python_files: List[str]
class RepositoryScanner:
    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path).resolve()
        self.excluded_directories = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            "dist",
            "build",
            ".idea",
            ".vscode",
            "migrations"
        }
    def is_excluded(self, path: Path) -> bool:
        return any(part in self.excluded_directories for part in path.parts)
    def get_all_files(self) -> List[Path]:
        return [
            path
            for path in self.repository_path.rglob("*")
            if path.is_file() and not self.is_excluded(path)
        ]
    def get_python_files(self) -> List[Path]:
        return [
            path
            for path in self.get_all_files()
            if path.suffix == ".py"
        ]
    def count_lines(self, file_path: Path) -> int:
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as file:
                return sum(1 for _ in file)
        except OSError:
            return 0
    def scan(self) -> RepositoryInfo:
        if not self.repository_path.exists():
            raise FileNotFoundError(f"Repository not found: {self.repository_path}")
        if not self.repository_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.repository_path}")
        all_files = self.get_all_files()
        python_files = self.get_python_files()
        total_lines = sum(self.count_lines(file) for file in python_files)
        relative_python_files = [
            str(file.relative_to(self.repository_path))
            for file in python_files
        ]
        return RepositoryInfo(
            path=str(self.repository_path),
            file_count=len(all_files),
            python_file_count=len(python_files),
            total_lines=total_lines,
            python_files=relative_python_files
        )