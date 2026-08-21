import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from git import Repo,GitCommandError
@dataclass
class RepositoryWorkspaceInfo:
    repository_url:str
    local_path:str
    branch:Optional[str]
    commit:str
class RepositoryWorkspace:
    def __init__(self,repository_url:str,branch:Optional[str]=None,depth:int=100):
        self.repository_url=repository_url
        self.branch=branch
        self.depth=depth
        self.temp_directory:Optional[str]=None
        self.repo:Optional[Repo]=None
    def __enter__(self):
        return self.clone()
    def __exit__(self,exc_type,exc_value,traceback):
        self.cleanup()
    def clone(self)->RepositoryWorkspaceInfo:
        self._validate_url()
        self.temp_directory=tempfile.mkdtemp(prefix="blastscope_repo_")
        clone_options={
            "url":self.repository_url,
            "to_path":self.temp_directory,
            "depth":self.depth,
            "single_branch":False
        }
        if self.branch:
            clone_options["branch"]=self.branch
            clone_options["single_branch"]=True
        try:
            self.repo=Repo.clone_from(**clone_options)
        except GitCommandError as error:
            self.cleanup()
            raise ValueError(f"Unable to clone repository: {error}") from error
        commit=self.repo.head.commit.hexsha
        current_branch=self._current_branch()
        return RepositoryWorkspaceInfo(
            repository_url=self.repository_url,
            local_path=self.temp_directory,
            branch=current_branch,
            commit=commit
        )
    def checkout(self,ref:str)->None:
        if not self.repo:
            raise RuntimeError("Repository has not been cloned")
        try:
            self.repo.git.checkout(ref)
        except GitCommandError as error:
            raise ValueError(f"Unable to checkout Git ref: {ref}") from error
    def fetch(self)->None:
        if not self.repo:
            raise RuntimeError("Repository has not been cloned")
        try:
            origin=self.repo.remotes.origin
            origin.fetch()
        except GitCommandError as error:
            raise ValueError(f"Unable to fetch repository updates: {error}") from error
    def cleanup(self)->None:
        if self.temp_directory and Path(self.temp_directory).exists():
            shutil.rmtree(self.temp_directory,ignore_errors=True)
        self.temp_directory=None
        self.repo=None
    def _current_branch(self)->Optional[str]:
        if not self.repo:
            return None
        if self.repo.head.is_detached:
            return None
        try:
            return self.repo.active_branch.name
        except TypeError:
            return None
    def _validate_url(self)->None:
        value=self.repository_url.strip()
        allowed_prefixes=(
            "https://",
            "http://",
            "git@"
        )
        if not value.startswith(allowed_prefixes):
            raise ValueError("Repository URL must use HTTPS, HTTP, or SSH")
        if len(value)>2048:
            raise ValueError("Repository URL is too long")