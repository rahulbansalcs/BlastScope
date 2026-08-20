from pathlib import Path
from typing import Dict,List
from app.graph.dependency_graph import DependencyGraph,DependencyNode
from app.parsers.python_parser import ParsedPythonFile
from app.symbols.symbol_table import SymbolTable
class GraphBuilder:
    def __init__(self,symbol_table:SymbolTable):
        self.symbol_table=symbol_table
        self.graph=DependencyGraph()
        self.file_nodes:Dict[str,str]={}
    def build(self,parsed_files:List[ParsedPythonFile])->DependencyGraph:
        self._create_file_nodes(parsed_files)
        self._create_symbol_nodes(parsed_files)
        self._create_import_edges(parsed_files)
        self._create_call_edges(parsed_files)
        return self.graph
    def _create_file_nodes(self,parsed_files:List[ParsedPythonFile])->None:
        for parsed_file in parsed_files:
            node_id=f"file:{parsed_file.module_name}"
            self.file_nodes[parsed_file.module_name]=node_id
            self.graph.add_node(
                DependencyNode(
                    id=node_id,
                    name=parsed_file.module_name,
                    node_type="file",
                    file_path=parsed_file.file_path
                )
            )
    def _create_symbol_nodes(self,parsed_files:List[ParsedPythonFile])->None:
        for parsed_file in parsed_files:
            file_node_id=self.file_nodes.get(parsed_file.module_name)
            for symbol in self.symbol_table.get_module_symbols(parsed_file.module_name):
                node_id=self._symbol_node_id(symbol.qualified_name)
                self.graph.add_node(
                    DependencyNode(
                        id=node_id,
                        name=symbol.qualified_name,
                        node_type=symbol.symbol_type,
                        file_path=symbol.file_path,
                        metadata={
                            "line_start":str(symbol.line_start),
                            "line_end":str(symbol.line_end)
                        }
                    )
                )
                if file_node_id:
                    self.graph.add_edge(
                        source=file_node_id,
                        target=node_id,
                        edge_type="contains"
                    )
    def _create_import_edges(self,parsed_files:List[ParsedPythonFile])->None:
        for parsed_file in parsed_files:
            source_file_id=self.file_nodes.get(parsed_file.module_name)
            if not source_file_id:
                continue
            for import_info in parsed_file.imports:
                target_module=import_info.module
                if not target_module:
                    continue
                target_file_id=self._resolve_module_file_node(target_module)
                if target_file_id:
                    self.graph.add_edge(
                        source=source_file_id,
                        target=target_file_id,
                        edge_type="imports"
                    )
    def _create_call_edges(self,parsed_files:List[ParsedPythonFile])->None:
        for parsed_file in parsed_files:
            for function in parsed_file.functions:
                self._connect_function_calls(
                    parsed_file.module_name,
                    function.qualified_name,
                    function.calls
                )
            for class_info in parsed_file.classes:
                for method in class_info.methods:
                    self._connect_function_calls(
                        parsed_file.module_name,
                        method.qualified_name,
                        method.calls
                    )
    def _connect_function_calls(self,module_name:str,caller_qualified_name:str,calls)->None:
        caller_id=self._symbol_node_id(caller_qualified_name)
        if caller_id not in self.graph.nodes:
            return
        for call in calls:
            resolved=self.symbol_table.resolve(module_name,call.name)
            if not resolved:
                continue
            target_id=self._symbol_node_id(resolved.qualified_name)
            if target_id not in self.graph.nodes:
                continue
            self.graph.add_edge(
                source=caller_id,
                target=target_id,
                edge_type="calls",
                confidence="confirmed"
            )
    def _resolve_module_file_node(self,module_name:str):
        if module_name in self.file_nodes:
            return self.file_nodes[module_name]
        parts=module_name.split(".")
        while parts:
            candidate=".".join(parts)
            if candidate in self.file_nodes:
                return self.file_nodes[candidate]
            parts.pop()
        return None
    def _symbol_node_id(self,qualified_name:str)->str:
        return f"symbol:{qualified_name}"