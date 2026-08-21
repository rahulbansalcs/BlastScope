from dataclasses import dataclass,field
from typing import List
from app.graph.dependency_graph import DependencyGraph
@dataclass
class CriticalComponent:
    node_id:str
    name:str
    node_type:str
    file_path:str
    direct_dependents:int
    direct_dependencies:int
    transitive_dependents:int
    api_endpoints:int
    dependency_depth:int
    criticality_score:int
    reasons:List[str]=field(default_factory=list)
@dataclass
class CriticalityAnalysis:
    components:List[CriticalComponent]=field(default_factory=list)
    total_components:int=0
class CriticalityAnalyzer:
    def analyze(self,graph:DependencyGraph,limit:int=20)->CriticalityAnalysis:
        components=[]
        for node_id,node in graph.nodes.items():
            if node.node_type not in {"function","method","class"}:
                continue
            direct_dependents=self._direct_dependents(graph,node_id)
            direct_dependencies=self._direct_dependencies(graph,node_id)
            transitive=graph.get_transitive_impact(node_id)
            transitive_dependents=len(transitive)
            dependency_depth=max((depth for _,depth in transitive),default=0)
            api_endpoints=sum(
                1
                for impacted_node,_ in transitive
                if impacted_node.node_type=="api_endpoint"
            )
            score=self._score(
                direct_dependents,
                direct_dependencies,
                transitive_dependents,
                api_endpoints,
                dependency_depth
            )
            reasons=self._reasons(
                direct_dependents,
                transitive_dependents,
                api_endpoints,
                dependency_depth
            )
            components.append(
                CriticalComponent(
                    node_id=node_id,
                    name=node.name,
                    node_type=node.node_type,
                    file_path=node.file_path,
                    direct_dependents=direct_dependents,
                    direct_dependencies=direct_dependencies,
                    transitive_dependents=transitive_dependents,
                    api_endpoints=api_endpoints,
                    dependency_depth=dependency_depth,
                    criticality_score=score,
                    reasons=reasons
                )
            )
        components.sort(
            key=lambda item:(
                item.criticality_score,
                item.transitive_dependents,
                item.direct_dependents
            ),
            reverse=True
        )
        if limit>0:
            components=components[:limit]
        return CriticalityAnalysis(
            components=components,
            total_components=len(components)
        )
    def _direct_dependents(self,graph:DependencyGraph,node_id:str)->int:
        return sum(
            1
            for edge in graph.incoming.get(node_id,[])
            if edge.edge_type in {"calls","routes_to"}
        )
    def _direct_dependencies(self,graph:DependencyGraph,node_id:str)->int:
        return sum(
            1
            for edge in graph.outgoing.get(node_id,[])
            if edge.edge_type=="calls"
        )
    def _score(self,direct_dependents:int,direct_dependencies:int,transitive_dependents:int,api_endpoints:int,dependency_depth:int)->int:
        direct_score=min(direct_dependents*12,30)
        transitive_score=min(transitive_dependents*4,30)
        api_score=min(api_endpoints*15,25)
        depth_score=min(dependency_depth*5,10)
        dependency_score=min(direct_dependencies*2,5)
        return min(
            100,
            direct_score+
            transitive_score+
            api_score+
            depth_score+
            dependency_score
        )
    def _reasons(self,direct_dependents:int,transitive_dependents:int,api_endpoints:int,dependency_depth:int)->List[str]:
        reasons=[]
        if direct_dependents>=3:
            reasons.append(f"{direct_dependents} components directly depend on this symbol")
        if transitive_dependents>=5:
            reasons.append(f"{transitive_dependents} components are in its transitive blast radius")
        if api_endpoints>0:
            reasons.append(f"{api_endpoints} public API endpoint(s) depend on this symbol")
        if dependency_depth>=3:
            reasons.append(f"Impact can propagate across {dependency_depth} dependency levels")
        if not reasons:
            reasons.append("Limited structural criticality detected")
        return reasons