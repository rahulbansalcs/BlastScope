import ast
from dataclasses import dataclass,field
from pathlib import Path
from typing import Dict,List,Optional
@dataclass
class FunctionSignature:
    qualified_name:str
    file_path:str
    line:int
    positional_args:List[str]=field(default_factory=list)
    keyword_only_args:List[str]=field(default_factory=list)
    defaults_count:int=0
    has_varargs:bool=False
    has_kwargs:bool=False
    is_async:bool=False
@dataclass
class SignatureChange:
    qualified_name:str
    change_type:str
    old_signature:Optional[FunctionSignature]
    new_signature:Optional[FunctionSignature]
    breaking:bool
    reasons:List[str]=field(default_factory=list)
class SignatureAnalyzer:
    def extract_from_source(self,source:str,file_path:str,module_name:str)->Dict[str,FunctionSignature]:
        tree=ast.parse(source,filename=file_path)
        signatures={}
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                signature=self._build_signature(node,file_path,module_name)
                signatures[signature.qualified_name]=signature
            elif isinstance(node,ast.ClassDef):
                for child in node.body:
                    if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                        signature=self._build_signature(child,file_path,module_name,node.name)
                        signatures[signature.qualified_name]=signature
        return signatures
    def extract_from_file(self,file_path:str,module_name:str)->Dict[str,FunctionSignature]:
        source=Path(file_path).read_text(encoding="utf-8",errors="ignore")
        return self.extract_from_source(source,file_path,module_name)
    def compare(self,old_signatures:Dict[str,FunctionSignature],new_signatures:Dict[str,FunctionSignature])->List[SignatureChange]:
        results=[]
        all_names=set(old_signatures)|set(new_signatures)
        for name in sorted(all_names):
            old=old_signatures.get(name)
            new=new_signatures.get(name)
            if old and not new:
                results.append(SignatureChange(qualified_name=name,change_type="removed",old_signature=old,new_signature=None,breaking=True,reasons=["Function or method was removed"]))
                continue
            if new and not old:
                results.append(SignatureChange(qualified_name=name,change_type="added",old_signature=None,new_signature=new,breaking=False,reasons=[]))
                continue
            if not old or not new:
                continue
            reasons=self._breaking_reasons(old,new)
            if self._signatures_equal(old,new):
                continue
            results.append(SignatureChange(qualified_name=name,change_type="modified",old_signature=old,new_signature=new,breaking=bool(reasons),reasons=reasons))
        return results
    def _build_signature(self,node,file_path:str,module_name:str,parent:Optional[str]=None)->FunctionSignature:
        positional=[arg.arg for arg in node.args.posonlyargs+node.args.args]
        keyword_only=[arg.arg for arg in node.args.kwonlyargs]
        qualified_name=f"{module_name}.{node.name}" if not parent else f"{module_name}.{parent}.{node.name}"
        return FunctionSignature(qualified_name=qualified_name,file_path=file_path,line=node.lineno,positional_args=positional,keyword_only_args=keyword_only,defaults_count=len(node.args.defaults),has_varargs=node.args.vararg is not None,has_kwargs=node.args.kwarg is not None,is_async=isinstance(node,ast.AsyncFunctionDef))
    def _breaking_reasons(self,old:FunctionSignature,new:FunctionSignature)->List[str]:
        reasons=[]
        old_required=len(old.positional_args)-old.defaults_count
        new_required=len(new.positional_args)-new.defaults_count
        if new_required>old_required:
            reasons.append(f"Required positional arguments increased from {old_required} to {new_required}")
        removed_args=[arg for arg in old.positional_args if arg not in new.positional_args]
        if removed_args:
            reasons.append(f"Arguments removed: {', '.join(removed_args)}")
        added_required=[arg for arg in new.positional_args if arg not in old.positional_args and new.positional_args.index(arg)<new_required]
        if added_required:
            reasons.append(f"New required arguments added: {', '.join(added_required)}")
        removed_keyword_only=[arg for arg in old.keyword_only_args if arg not in new.keyword_only_args]
        if removed_keyword_only:
            reasons.append(f"Keyword-only arguments removed: {', '.join(removed_keyword_only)}")
        if old.has_varargs and not new.has_varargs:
            reasons.append("Variable positional arguments support was removed")
        if old.has_kwargs and not new.has_kwargs:
            reasons.append("Variable keyword arguments support was removed")
        if old.is_async!=new.is_async:
            reasons.append("Function async behavior changed")
        return reasons
    def _signatures_equal(self,old:FunctionSignature,new:FunctionSignature)->bool:
        return old.positional_args==new.positional_args and old.keyword_only_args==new.keyword_only_args and old.defaults_count==new.defaults_count and old.has_varargs==new.has_varargs and old.has_kwargs==new.has_kwargs and old.is_async==new.is_async