from dataclasses import dataclass,field
from pathlib import Path
from typing import Dict,List,Optional
from app.graph.dependency_graph import DependencyGraph
@dataclass
class ArchitectureRule:
    source_layer:str
    allowed_targets:List[str]=field(default_factory=list)
@dataclass
class ArchitectureViolation:
    source_node:str
    target_node:str
    source_layer:str
    target_layer:str
    edge_type:str
    file_path:str
    reason:str
@dataclass
class ArchitectureAnalysis:
    violations:List[ArchitectureViolation]=field(default_factory=list)
    total_violations:int=0
class ArchitectureAnalyzer:
    def __init__(self):
        self.rules={
            "routes":ArchitectureRule(
                source_layer="routes",
                allowed_targets=["services","schemas","utils"]
            ),
            "controllers":ArchitectureRule(
                source_layer="controllers",
                allowed_targets=["services","schemas","utils"]
            ),
            "services":ArchitectureRule(
                source_layer="services",
                allowed_targets=["repositories","models","schemas","utils"]
            ),
            "repositories":ArchitectureRule(
                source_layer="repositories",
                allowed_targets=["models","database","utils"]
            ),
            "models":ArchitectureRule(
                source_layer="models",
                allowed_targets=["utils"]
            ),
            "database":ArchitectureRule(
                source_layer="database",
                allowed_targets=["models","utils"]
            )
        }
    def analyze(self,graph:DependencyGraph)->ArchitectureAnalysis:
        violations=[]
        for source_id,edges in graph.outgoing.items():
            source_node=graph.get_node(source_id)
            if not source_node:
                continue
            source_layer=self._detect_layer(source_node.file_path)
            if not source_layer:
                continue
            rule=self.rules.get(source_layer)
            if not rule:
                continue
            for edge in edges:
                if edge.edge_type not in {"calls","imports"}:
                    continue
                target_node=graph.get_node(edge.target)
                if not target_node:
                    continue
                target_layer=self._detect_layer(target_node.file_path)
                if not target_layer:
                    continue
                if source_layer==target_layer:
                    continue
                if target_layer not in rule.allowed_targets:
                    violations.append(
                        ArchitectureViolation(
                            source_node=source_node.name,
                            target_node=target_node.name,
                            source_layer=source_layer,
                            target_layer=target_layer,
                            edge_type=edge.edge_type,
                            file_path=source_node.file_path,
                            reason=f"{source_layer} should not directly depend on {target_layer}"
                        )
                    )
        return ArchitectureAnalysis(
            violations=violations,
            total_violations=len(violations)
        )
    def violations_for_node(self,graph:DependencyGraph,node_id:str)->List[ArchitectureViolation]:
        analysis=self.analyze(graph)
        node=graph.get_node(node_id)
        if not node:
            return []
        return [
            violation
            for violation in analysis.violations
            if violation.source_node==node.name or violation.target_node==node.name
        ]
    def _detect_layer(self,file_path:str)->Optional[str]:
        normalized=Path(file_path).as_posix().lower()
        parts=normalized.split("/")
        candidates={
            "routes",
            "controllers",
            "services",
            "repositories",
            "models",
            "database",
            "schemas",
            "utils"
        }
        for part in parts:
            if part in candidates:
                return part
        return None