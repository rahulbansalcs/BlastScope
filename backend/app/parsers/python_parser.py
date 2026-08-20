import ast
from dataclasses import dataclass,field
from pathlib import Path
from typing import List,Optional
@dataclass
class ImportInfo:
    module:str
    name:Optional[str]
    alias:Optional[str]
    line:int
@dataclass
class FunctionCallInfo:
    name:str
    line:int
@dataclass
class FunctionInfo:
    name:str
    qualified_name:str
    line_start:int
    line_end:int
    is_async:bool
    decorators:List[str]=field(default_factory=list)
    calls:List[FunctionCallInfo]=field(default_factory=list)
@dataclass
class ClassInfo:
    name:str
    qualified_name:str
    line_start:int
    line_end:int
    bases:List[str]=field(default_factory=list)
    methods:List[FunctionInfo]=field(default_factory=list)
@dataclass
class ParsedPythonFile:
    file_path:str
    module_name:str
    imports:List[ImportInfo]=field(default_factory=list)
    functions:List[FunctionInfo]=field(default_factory=list)
    classes:List[ClassInfo]=field(default_factory=list)
    syntax_error:Optional[str]=None
class PythonParser:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
    def parse_file(self,file_path:str)->ParsedPythonFile:
        path=Path(file_path).resolve()
        module_name=self._build_module_name(path)
        result=ParsedPythonFile(file_path=str(path),module_name=module_name)
        try:
            source=path.read_text(encoding="utf-8",errors="ignore")
            tree=ast.parse(source,filename=str(path))
        except SyntaxError as error:
            result.syntax_error=str(error)
            return result
        for node in tree.body:
            if isinstance(node,ast.Import):
                result.imports.extend(self._parse_import(node))
            elif isinstance(node,ast.ImportFrom):
                result.imports.extend(self._parse_import_from(node))
            elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                result.functions.append(self._parse_function(node,module_name))
            elif isinstance(node,ast.ClassDef):
                result.classes.append(self._parse_class(node,module_name))
        return result
    def _parse_import(self,node:ast.Import)->List[ImportInfo]:
        return [ImportInfo(module=item.name,name=None,alias=item.asname,line=node.lineno) for item in node.names]
    def _parse_import_from(self,node:ast.ImportFrom)->List[ImportInfo]:
        module=node.module or ""
        return [ImportInfo(module=module,name=item.name,alias=item.asname,line=node.lineno) for item in node.names]
    def _parse_function(self,node,module_name:str,parent:Optional[str]=None)->FunctionInfo:
        qualified_name=f"{module_name}.{node.name}" if not parent else f"{module_name}.{parent}.{node.name}"
        decorators=[self._expression_name(item) for item in node.decorator_list]
        calls=[]
        for child in ast.walk(node):
            if isinstance(child,ast.Call):
                calls.append(FunctionCallInfo(name=self._expression_name(child.func),line=getattr(child,"lineno",0)))
        return FunctionInfo(name=node.name,qualified_name=qualified_name,line_start=node.lineno,line_end=getattr(node,"end_lineno",node.lineno),is_async=isinstance(node,ast.AsyncFunctionDef),decorators=decorators,calls=calls)
    def _parse_class(self,node:ast.ClassDef,module_name:str)->ClassInfo:
        methods=[]
        for child in node.body:
            if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                methods.append(self._parse_function(child,module_name,node.name))
        bases=[self._expression_name(base) for base in node.bases]
        return ClassInfo(name=node.name,qualified_name=f"{module_name}.{node.name}",line_start=node.lineno,line_end=getattr(node,"end_lineno",node.lineno),bases=bases,methods=methods)
    def _expression_name(self,node:ast.AST)->str:
        if isinstance(node,ast.Name):
            return node.id
        if isinstance(node,ast.Attribute):
            parent=self._expression_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        if isinstance(node,ast.Call):
            return self._expression_name(node.func)
        if isinstance(node,ast.Subscript):
            return self._expression_name(node.value)
        return ""
    def _build_module_name(self,path:Path)->str:
        try:
            relative=path.relative_to(self.repository_path)
        except ValueError:
            relative=path
        parts=list(relative.with_suffix("").parts)
        if parts and parts[-1]=="__init__":
            parts=parts[:-1]
        return ".".join(parts)