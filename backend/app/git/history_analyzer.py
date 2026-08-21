from dataclasses import dataclass,field
from pathlib import Path
from typing import Dict,List
from git import Repo
@dataclass
class FileHistory:
    file_path:str
    commit_count:int
    contributors:int
    bugfix_commits:int
    revert_commits:int
    instability_score:int
    recent_commits:List[str]=field(default_factory=list)
class GitHistoryAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
    def analyze_file(self,file_path:str,max_commits:int=200)->FileHistory:
        commits=list(self.repo.iter_commits(paths=file_path,max_count=max_commits))
        contributors=set()
        bugfix_count=0
        revert_count=0
        recent=[]
        for commit in commits:
            if commit.author.email:
                contributors.add(commit.author.email)
            message=commit.message.strip().lower()
            if self._is_bugfix(message):
                bugfix_count+=1
            if self._is_revert(message):
                revert_count+=1
            if len(recent)<10:
                recent.append(f"{commit.hexsha[:8]} {commit.summary}")
        score=self._calculate_instability(
            len(commits),
            len(contributors),
            bugfix_count,
            revert_count
        )
        return FileHistory(
            file_path=file_path,
            commit_count=len(commits),
            contributors=len(contributors),
            bugfix_commits=bugfix_count,
            revert_commits=revert_count,
            instability_score=score,
            recent_commits=recent
        )
    def analyze_files(self,file_paths:List[str])->Dict[str,FileHistory]:
        results={}
        for file_path in file_paths:
            results[file_path]=self.analyze_file(file_path)
        return results
    def _is_bugfix(self,message:str)->bool:
        keywords={
            "fix",
            "bug",
            "hotfix",
            "patch",
            "issue",
            "error",
            "crash"
        }
        return any(keyword in message for keyword in keywords)
    def _is_revert(self,message:str)->bool:
        return "revert" in message or "rollback" in message
    def _calculate_instability(self,commit_count:int,contributors:int,bugfix_count:int,revert_count:int)->int:
        commit_score=min(commit_count*3,40)
        contributor_score=min(contributors*5,20)
        bugfix_score=min(bugfix_count*8,30)
        revert_score=min(revert_count*10,30)
        return min(100,commit_score+contributor_score+bugfix_score+revert_score)