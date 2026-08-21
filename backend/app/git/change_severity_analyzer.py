from dataclasses import dataclass,field
from pathlib import Path
from typing import List
from git import Repo
@dataclass
class FileChangeSeverity:
    file_path:str
    additions:int
    deletions:int
    total_changed_lines:int
    change_ratio:float
    severity_score:int
    severity_level:str
    reasons:List[str]=field(default_factory=list)
@dataclass
class ChangeSeverityResult:
    base_ref:str
    target_ref:str
    files:List[FileChangeSeverity]=field(default_factory=list)
class ChangeSeverityAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
    def analyze(self,base_ref:str="main",target_ref:str="HEAD")->ChangeSeverityResult:
        base=self.repo.commit(base_ref)
        target=self.repo.commit(target_ref)
        diff=base.diff(target,create_patch=True)
        results=[]
        for item in diff:
            file_path=item.b_path or item.a_path
            if not file_path:
                continue
            additions,deletions=self._count_changes(item.diff)
            total=additions+deletions
            target_lines=self._file_line_count(target_ref,file_path)
            ratio=(total/max(target_lines,1))*100
            score=self._score(total,ratio,additions,deletions)
            level=self._level(score)
            reasons=self._reasons(total,ratio,additions,deletions)
            results.append(
                FileChangeSeverity(
                    file_path=file_path,
                    additions=additions,
                    deletions=deletions,
                    total_changed_lines=total,
                    change_ratio=round(ratio,2),
                    severity_score=score,
                    severity_level=level,
                    reasons=reasons
                )
            )
        results.sort(key=lambda item:item.severity_score,reverse=True)
        return ChangeSeverityResult(
            base_ref=base_ref,
            target_ref=target_ref,
            files=results
        )
    def analyze_file(self,file_path:str,base_ref:str="main",target_ref:str="HEAD"):
        result=self.analyze(base_ref,target_ref)
        normalized=str(Path(file_path))
        for item in result.files:
            if str(Path(item.file_path))==normalized:
                return item
        return None
    def _count_changes(self,patch:bytes):
        additions=0
        deletions=0
        if not patch:
            return additions,deletions
        text=patch.decode("utf-8",errors="ignore")
        for line in text.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                additions+=1
            elif line.startswith("-"):
                deletions+=1
        return additions,deletions
    def _file_line_count(self,ref:str,file_path:str)->int:
        try:
            blob=self.repo.commit(ref).tree/file_path
            source=blob.data_stream.read().decode("utf-8",errors="ignore")
            return max(len(source.splitlines()),1)
        except Exception:
            return 1
    def _score(self,total:int,ratio:float,additions:int,deletions:int)->int:
        line_score=0
        if total<=5:
            line_score=10
        elif total<=20:
            line_score=30
        elif total<=50:
            line_score=50
        elif total<=100:
            line_score=75
        else:
            line_score=100
        ratio_score=0
        if ratio<=5:
            ratio_score=10
        elif ratio<=15:
            ratio_score=30
        elif ratio<=30:
            ratio_score=50
        elif ratio<=60:
            ratio_score=75
        else:
            ratio_score=100
        rewrite_score=0
        if additions>0 and deletions>0:
            rewrite_ratio=min(additions,deletions)/max(additions,deletions)
            if rewrite_ratio>=0.75:
                rewrite_score=100
            elif rewrite_ratio>=0.5:
                rewrite_score=70
            elif rewrite_ratio>=0.25:
                rewrite_score=40
        total_score=(line_score*0.45)+(ratio_score*0.40)+(rewrite_score*0.15)
        return min(100,round(total_score))
    def _level(self,score:int)->str:
        if score<=25:
            return "LOW"
        if score<=50:
            return "MEDIUM"
        if score<=75:
            return "HIGH"
        return "CRITICAL"
    def _reasons(self,total:int,ratio:float,additions:int,deletions:int)->List[str]:
        reasons=[]
        reasons.append(f"{total} lines changed")
        reasons.append(f"{round(ratio,2)}% of the target file changed")
        if additions>50:
            reasons.append(f"Large addition surface with {additions} added lines")
        if deletions>50:
            reasons.append(f"Large deletion surface with {deletions} removed lines")
        if additions>0 and deletions>0:
            rewrite_ratio=min(additions,deletions)/max(additions,deletions)
            if rewrite_ratio>=0.5:
                reasons.append("Change resembles a significant rewrite rather than a small patch")
        return reasons