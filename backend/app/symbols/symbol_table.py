from dataclasses import dataclass,field
from typing import Dict,List,Optional
from app.parsers.python_parser import ParsedPythonFile
@dataclass
class Symbol:
    name:str
    qualified_name:str
    symbol_type:str
    file_path:str
    line_start:int
    line_end:int
    parent:Optional[str]=None
@dataclass
class ModuleSymbols:
    module_name:str
    file_path:str
    symbols:List[Symbol]=field(default_factory=list)
    aliases:Dict[str,str]=field(default_factory=dict)
class SymbolTable:
    def __init__(self):
        self.modules:Dict[str,ModuleSymbols]={}
        self.symbols_by_qualified_name:Dict[str,Symbol]={}
        self.symbols_by_simple_name:Dict[str,List[Symbol]]={}
    def add_parsed_file(self,parsed_file:ParsedPythonFile)->None:
        module=ModuleSymbols(module_name=parsed_file.module_name,file_path=parsed_file.file_path)
        for import_info in parsed_file.imports:
            target=self._build_import_target(import_info.module,import_info.name)
            visible_name=import_info.alias or import_info.name or import_info.module.split(".")[-1]
            if visible_name:
                module.aliases[visible_name]=target
        for function in parsed_file.functions:
            symbol=Symbol(name=function.name,qualified_name=function.qualified_name,symbol_type="function",file_path=parsed_file.file_path,line_start=function.line_start,line_end=function.line_end)
            self._register_symbol(module,symbol)
        for class_info in parsed_file.classes:
            class_symbol=Symbol(name=class_info.name,qualified_name=class_info.qualified_name,symbol_type="class",file_path=parsed_file.file_path,line_start=class_info.line_start,line_end=class_info.line_end)
            self._register_symbol(module,class_symbol)
            for method in class_info.methods:
                method_symbol=Symbol(name=method.name,qualified_name=method.qualified_name,symbol_type="method",file_path=parsed_file.file_path,line_start=method.line_start,line_end=method.line_end,parent=class_info.qualified_name)
                self._register_symbol(module,method_symbol)
        self.modules[parsed_file.module_name]=module
    def resolve(self,module_name:str,name:str)->Optional[Symbol]:
        module=self.modules.get(module_name)
        if module:
            direct=f"{module_name}.{name}"
            if direct in self.symbols_by_qualified_name:
                return self.symbols_by_qualified_name[direct]
            alias_target=module.aliases.get(name)
            if alias_target:
                resolved=self._resolve_import_target(module_name,alias_target)
                if resolved:
                    return resolved
            if "." in name:
                first,*rest=name.split(".")
                alias_target=module.aliases.get(first)
                if alias_target:
                    candidate=".".join([alias_target,*rest])
                    resolved=self._resolve_import_target(module_name,candidate)
                    if resolved:
                        return resolved
        matches=self.symbols_by_simple_name.get(name,[])
        if len(matches)==1:
            return matches[0]
        return None
    def get_symbol(self,qualified_name:str)->Optional[Symbol]:
        return self.symbols_by_qualified_name.get(qualified_name)
    def get_module_symbols(self,module_name:str)->List[Symbol]:
        module=self.modules.get(module_name)
        return module.symbols if module else []
    def get_all_symbols(self)->List[Symbol]:
        return list(self.symbols_by_qualified_name.values())
    def _resolve_import_target(self,current_module:str,target:str)->Optional[Symbol]:
        if target in self.symbols_by_qualified_name:
            return self.symbols_by_qualified_name[target]
        current_parts=current_module.split(".")[:-1]
        target_parts=target.split(".")
        while current_parts:
            candidate=".".join(current_parts+target_parts)
            if candidate in self.symbols_by_qualified_name:
                return self.symbols_by_qualified_name[candidate]
            current_parts.pop()
        suffix=f".{target}"
        matches=[
            symbol
            for qualified_name,symbol in self.symbols_by_qualified_name.items()
            if qualified_name.endswith(suffix)
        ]
        if len(matches)==1:
            return matches[0]
        return None
    def _register_symbol(self,module:ModuleSymbols,symbol:Symbol)->None:
        module.symbols.append(symbol)
        self.symbols_by_qualified_name[symbol.qualified_name]=symbol
        self.symbols_by_simple_name.setdefault(symbol.name,[]).append(symbol)
    def _build_import_target(self,module:str,name:Optional[str])->str:
        if name:
            return f"{module}.{name}" if module else name
        return module