from dataclasses import dataclass,field
from pathlib import Path
from typing import List
from app.git.diff_analyzer import GitDiffResult,ChangedFile
from app.parsers.python_parser import ParsedPythonFile
@dataclass
class ChangedSymbol:
    qualified_name:str
    symbol_type:str
    file_path:str
    line_start:int
    line_end:int
    change_type:str
@dataclass
class ChangeMappingResult:
    changed_symbols:List[ChangedSymbol]=field(default_factory=list)
    unmapped_files:List[str]=field(default_factory=list)
class ChangeMapper:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
    def map_changes(self,diff_result:GitDiffResult,parsed_files:List[ParsedPythonFile])->ChangeMappingResult:
        result=ChangeMappingResult()
        parsed_by_path=self._build_file_index(parsed_files)
        for changed_file in diff_result.changed_files:
            normalized_path=self._normalize_path(changed_file.path)
            parsed_file=parsed_by_path.get(normalized_path)
            if not parsed_file:
                result.unmapped_files.append(changed_file.path)
                continue
            mapped=self._map_file_symbols(changed_file,parsed_file)
            result.changed_symbols.extend(mapped)
        result.changed_symbols=self._deduplicate(result.changed_symbols)
        return result
    def _build_file_index(self,parsed_files:List[ParsedPythonFile])->dict[str,ParsedPythonFile]:
        index={}
        for parsed_file in parsed_files:
            path=Path(parsed_file.file_path).resolve()
            try:
                relative=path.relative_to(self.repository_path)
                index[str(relative)]=parsed_file
            except ValueError:
                continue
        return index
    def _normalize_path(self,path:str)->str:
        normalized=Path(path)
        parts=normalized.parts
        if parts and parts[0]=="backend":
            normalized=Path(*parts[1:])
        return str(normalized)
    def _map_file_symbols(self,changed_file:ChangedFile,parsed_file:ParsedPythonFile)->List[ChangedSymbol]:
        changed_symbols=[]
        if changed_file.change_type=="deleted":
            return changed_symbols
        for function in parsed_file.functions:
            if self._symbol_changed(function.line_start,function.line_end,changed_file):
                changed_symbols.append(
                    ChangedSymbol(
                        qualified_name=function.qualified_name,
                        symbol_type="function",
                        file_path=parsed_file.file_path,
                        line_start=function.line_start,
                        line_end=function.line_end,
                        change_type=changed_file.change_type
                    )
                )
        for class_info in parsed_file.classes:
            if self._symbol_changed(class_info.line_start,class_info.line_end,changed_file):
                changed_symbols.append(
                    ChangedSymbol(
                        qualified_name=class_info.qualified_name,
                        symbol_type="class",
                        file_path=parsed_file.file_path,
                        line_start=class_info.line_start,
                        line_end=class_info.line_end,
                        change_type=changed_file.change_type
                    )
                )
            for method in class_info.methods:
                if self._symbol_changed(method.line_start,method.line_end,changed_file):
                    changed_symbols.append(
                        ChangedSymbol(
                            qualified_name=method.qualified_name,
                            symbol_type="method",
                            file_path=parsed_file.file_path,
                            line_start=method.line_start,
                            line_end=method.line_end,
                            change_type=changed_file.change_type
                        )
                    )
        return changed_symbols
    def _symbol_changed(self,line_start:int,line_end:int,changed_file:ChangedFile)->bool:
        for line_range in changed_file.changed_lines:
            if line_start<=line_range.end and line_end>=line_range.start:
                return True
        return False
    def _deduplicate(self,symbols:List[ChangedSymbol])->List[ChangedSymbol]:
        unique={}
        for symbol in symbols:
            unique[symbol.qualified_name]=symbol
        return list(unique.values())