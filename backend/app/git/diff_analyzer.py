from dataclasses import dataclass,field
from pathlib import Path
from typing import List,Optional
from git import Repo,GitCommandError
@dataclass
class ChangedLineRange:
    start:int
    end:int
@dataclass
class ChangedFile:
    path:str
    change_type:str
    old_path:Optional[str]=None
    changed_lines:List[ChangedLineRange]=field(default_factory=list)
@dataclass
class GitDiffResult:
    base_ref:str
    target_ref:str
    changed_files:List[ChangedFile]=field(default_factory=list)
class GitDiffAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
    def analyze(self,base_ref:str="main",target_ref:str="HEAD")->GitDiffResult:
        self._validate_ref(base_ref)
        self._validate_ref(target_ref)
        diff_index=self.repo.commit(base_ref).diff(self.repo.commit(target_ref),create_patch=True)
        changed_files=[]
        for diff in diff_index:
            path=diff.b_path or diff.a_path
            old_path=diff.a_path if diff.a_path!=diff.b_path else None
            change_type=self._detect_change_type(diff)
            line_ranges=self._extract_changed_lines(diff.diff)
            changed_files.append(
                ChangedFile(
                    path=path or "",
                    change_type=change_type,
                    old_path=old_path,
                    changed_lines=line_ranges
                )
            )
        return GitDiffResult(
            base_ref=base_ref,
            target_ref=target_ref,
            changed_files=changed_files
        )
    def get_current_branch(self)->str:
        if self.repo.head.is_detached:
            return "HEAD"
        return self.repo.active_branch.name
    def get_current_commit(self)->str:
        return self.repo.head.commit.hexsha
    def _detect_change_type(self,diff)->str:
        if diff.new_file:
            return "added"
        if diff.deleted_file:
            return "deleted"
        if diff.renamed_file:
            return "renamed"
        return "modified"
    def _extract_changed_lines(self,patch:bytes)->List[ChangedLineRange]:
        if not patch:
            return []
        text=patch.decode("utf-8",errors="ignore")
        ranges=[]
        for line in text.splitlines():
            if not line.startswith("@@"):
                continue
            try:
                new_section=line.split("+")[1].split(" ")[0]
                if "," in new_section:
                    start_text,count_text=new_section.split(",",1)
                    start=int(start_text)
                    count=int(count_text)
                else:
                    start=int(new_section)
                    count=1
                end=start+max(count-1,0)
                ranges.append(ChangedLineRange(start=start,end=end))
            except (IndexError,ValueError):
                continue
        return ranges
    def _validate_ref(self,ref:str)->None:
        try:
            self.repo.commit(ref)
        except (ValueError,GitCommandError) as error:
            raise ValueError(f"Invalid Git reference: {ref}") from error