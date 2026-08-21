import ast
from dataclasses import dataclass,field
from pathlib import Path
from typing import Dict,List,Optional,Tuple
from git import Repo
@dataclass
class SymbolSnapshot:
    qualified_name:str
    name:str
    symbol_type:str
    file_path:str
    line_start:int
    line_end:int
    signature:str
@dataclass
class SymbolChange:
    change_type:str
    old_symbol:Optional[SymbolSnapshot]
    new_symbol:Optional[SymbolSnapshot]
    confidence:float
    breaking:bool
    reasons:List[str]=field(default_factory=list)
@dataclass
class SymbolChangeAnalysis:
    base_ref:str
    target_ref:str
    changes:List[SymbolChange]=field(default_factory=list)
class SymbolChangeAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
    def analyze(self,base_ref:str="main",target_ref:str="HEAD")->SymbolChangeAnalysis:
        old_symbols=self._snapshot_repository(base_ref)
        new_symbols=self._snapshot_repository(target_ref)
        changes=[]
        deleted={
            name:symbol
            for name,symbol in old_symbols.items()
            if name not in new_symbols
        }
        added={
            name:symbol
            for name,symbol in new_symbols.items()
            if name not in old_symbols
        }
        matched_added=set()
        for old_name,old_symbol in deleted.items():
            rename_candidate=self._find_rename_candidate(old_symbol,added,matched_added)
            if rename_candidate:
                new_name,new_symbol,confidence=rename_candidate
                matched_added.add(new_name)
                changes.append(
                    SymbolChange(
                        change_type="renamed",
                        old_symbol=old_symbol,
                        new_symbol=new_symbol,
                        confidence=confidence,
                        breaking=True,
                        reasons=[
                            f"Symbol name changed from {old_symbol.name} to {new_symbol.name}",
                            "Existing imports or callers may still reference the old symbol"
                        ]
                    )
                )
            else:
                changes.append(
                    SymbolChange(
                        change_type="deleted",
                        old_symbol=old_symbol,
                        new_symbol=None,
                        confidence=100.0,
                        breaking=True,
                        reasons=[
                            "Symbol no longer exists in the target revision",
                            "Existing callers may fail at import time or runtime"
                        ]
                    )
                )
        for new_name,new_symbol in added.items():
            if new_name in matched_added:
                continue
            changes.append(
                SymbolChange(
                    change_type="added",
                    old_symbol=None,
                    new_symbol=new_symbol,
                    confidence=100.0,
                    breaking=False,
                    reasons=[]
                )
            )
        return SymbolChangeAnalysis(
            base_ref=base_ref,
            target_ref=target_ref,
            changes=changes
        )
    def _snapshot_repository(self,ref:str)->Dict[str,SymbolSnapshot]:
        commit=self.repo.commit(ref)
        symbols={}
        for item in commit.tree.traverse():
            if item.type!="blob":
                continue
            if not item.path.endswith(".py"):
                continue
            try:
                source=item.data_stream.read().decode("utf-8",errors="ignore")
                tree=ast.parse(source,filename=item.path)
            except Exception:
                continue
            module_name=self._module_name(item.path)
            for node in tree.body:
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    symbol=self._function_snapshot(node,module_name,item.path)
                    symbols[symbol.qualified_name]=symbol
                elif isinstance(node,ast.ClassDef):
                    class_symbol=SymbolSnapshot(
                        qualified_name=f"{module_name}.{node.name}",
                        name=node.name,
                        symbol_type="class",
                        file_path=item.path,
                        line_start=node.lineno,
                        line_end=getattr(node,"end_lineno",node.lineno),
                        signature=node.name
                    )
                    symbols[class_symbol.qualified_name]=class_symbol
                    for child in node.body:
                        if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                            symbol=self._function_snapshot(
                                child,
                                module_name,
                                item.path,
                                node.name
                            )
                            symbols[symbol.qualified_name]=symbol
        return symbols
    def _function_snapshot(self,node,module_name:str,file_path:str,parent:Optional[str]=None)->SymbolSnapshot:
        positional=[arg.arg for arg in node.args.posonlyargs+node.args.args]
        keyword_only=[arg.arg for arg in node.args.kwonlyargs]
        signature="|".join(
            positional+
            keyword_only+
            [
                f"defaults:{len(node.args.defaults)}",
                f"varargs:{node.args.vararg is not None}",
                f"kwargs:{node.args.kwarg is not None}",
                f"async:{isinstance(node,ast.AsyncFunctionDef)}"
            ]
        )
        qualified_name=f"{module_name}.{node.name}" if not parent else f"{module_name}.{parent}.{node.name}"
        return SymbolSnapshot(
            qualified_name=qualified_name,
            name=node.name,
            symbol_type="method" if parent else "function",
            file_path=file_path,
            line_start=node.lineno,
            line_end=getattr(node,"end_lineno",node.lineno),
            signature=signature
        )
    def _find_rename_candidate(self,old_symbol:SymbolSnapshot,added:Dict[str,SymbolSnapshot],matched_added:set)->Optional[Tuple[str,SymbolSnapshot,float]]:
        best=None
        best_score=0.0
        for new_name,new_symbol in added.items():
            if new_name in matched_added:
                continue
            if old_symbol.symbol_type!=new_symbol.symbol_type:
                continue
            score=0.0
            if old_symbol.file_path==new_symbol.file_path:
                score+=45
            if old_symbol.signature==new_symbol.signature:
                score+=40
            old_parent=self._parent_name(old_symbol.qualified_name)
            new_parent=self._parent_name(new_symbol.qualified_name)
            if old_parent==new_parent:
                score+=15
            if score>best_score:
                best_score=score
                best=(new_name,new_symbol,score)
        if best and best_score>=70:
            return best
        return None
    def _parent_name(self,qualified_name:str)->str:
        parts=qualified_name.split(".")
        if len(parts)<=1:
            return ""
        return ".".join(parts[:-1])
    def _module_name(self,file_path:str)->str:
        path=Path(file_path)
        parts=list(path.with_suffix("").parts)
        if parts and parts[0]=="backend":
            parts=parts[1:]
        if parts and parts[-1]=="__init__":
            parts=parts[:-1]
        return ".".join(parts)