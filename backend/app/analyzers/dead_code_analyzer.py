from dataclasses import dataclass,field
from typing import List
from app.graph.dependency_graph import DependencyGraph
@dataclass
class DeadCodeCandidate:
    node_id:str
    name:str
    node_type:str
    file_path:str
    incoming_dependencies:int
    outgoing_dependencies:int
    confidence:str
    reasons:List[str]=field(default_factory=list)
@dataclass
class DeadCodeAnalysis:
    candidates:List[DeadCodeCandidate]=field(default_factory=list)
    total_candidates:int=0
class DeadCodeAnalyzer:
    def analyze(self,graph:DependencyGraph)->DeadCodeAnalysis:
        candidates=[]
        for node_id,node in graph.nodes.items():
            if node.node_type not in {"function","method","class"}:
                continue
            if self._should_ignore(node.name,node.file_path):
                continue
            incoming=self._meaningful_incoming(graph,node_id)
            outgoing=self._meaningful_outgoing(graph,node_id)
            if incoming:
                continue
            reasons=[]
            reasons.append("No incoming call or route dependencies detected")
            if not outgoing:
                reasons.append("No outgoing code dependencies detected")
            confidence=self._confidence(node.name,node.node_type,outgoing)
            candidates.append(
                DeadCodeCandidate(
                    node_id=node_id,
                    name=node.name,
                    node_type=node.node_type,
                    file_path=node.file_path,
                    incoming_dependencies=len(incoming),
                    outgoing_dependencies=len(outgoing),
                    confidence=confidence,
                    reasons=reasons
                )
            )
        candidates.sort(key=lambda item:(self._confidence_rank(item.confidence),item.name))
        return DeadCodeAnalysis(
            candidates=candidates,
            total_candidates=len(candidates)
        )
    def analyze_node(self,graph:DependencyGraph,node_id:str):
        result=self.analyze(graph)
        for candidate in result.candidates:
            if candidate.node_id==node_id:
                return candidate
        return None
    def _meaningful_incoming(self,graph:DependencyGraph,node_id:str):
        return [
            edge
            for edge in graph.incoming.get(node_id,[])
            if edge.edge_type in {"calls","routes_to"}
        ]
    def _meaningful_outgoing(self,graph:DependencyGraph,node_id:str):
        return [
            edge
            for edge in graph.outgoing.get(node_id,[])
            if edge.edge_type=="calls"
        ]
    def _should_ignore(self,name:str,file_path:str)->bool:
        simple_name=name.rsplit(".",1)[-1]
        ignored_names={
            "__init__",
            "__enter__",
            "__exit__",
            "__str__",
            "__repr__",
            "__iter__",
            "__next__",
            "__len__",
            "main"
        }
        if simple_name in ignored_names:
            return True
        if simple_name.startswith("test_"):
            return True
        normalized=file_path.replace("\\","/").lower()
        if "/tests/" in normalized or normalized.endswith("_test.py") or "/test_" in normalized:
            return True
        return False
    def _confidence(self,name:str,node_type:str,outgoing)->str:
        simple=name.rsplit(".",1)[-1]
        if simple.startswith("_"):
            return "HIGH"
        if node_type=="function" and not outgoing:
            return "HIGH"
        if node_type=="method":
            return "MEDIUM"
        if node_type=="class":
            return "MEDIUM"
        return "LOW"
    def _confidence_rank(self,confidence:str)->int:
        ranks={
            "HIGH":0,
            "MEDIUM":1,
            "LOW":2
        }
        return ranks.get(confidence,3)