from dataclasses import dataclass,field
from typing import List,Dict,Optional
from app.graph.dependency_graph import DependencyGraph,DependencyNode
@dataclass
class ImpactedComponent:
    id:str
    name:str
    node_type:str
    file_path:str
    depth:int
@dataclass
class ImpactAnalysis:
    target_id:str
    target_name:str
    direct_impact:List[ImpactedComponent]=field(default_factory=list)
    indirect_impact:List[ImpactedComponent]=field(default_factory=list)
    affected_files:List[str]=field(default_factory=list)
    affected_functions:List[str]=field(default_factory=list)
    affected_classes:List[str]=field(default_factory=list)
    affected_endpoints:List[str]=field(default_factory=list)
    total_affected:int=0
    maximum_depth:int=0
class ImpactEngine:
    def __init__(self,graph:DependencyGraph):
        self.graph=graph
    def analyze(self,node_id:str,max_depth:Optional[int]=None)->ImpactAnalysis:
        target=self.graph.get_node(node_id)
        if not target:
            raise ValueError(f"Node not found: {node_id}")
        impacted=self.graph.get_transitive_impact(node_id,max_depth=max_depth)
        direct=[]
        indirect=[]
        affected_files=set()
        affected_functions=set()
        affected_classes=set()
        affected_endpoints=set()
        maximum_depth=0
        for node,depth in impacted:
            component=self._to_component(node,depth)
            maximum_depth=max(maximum_depth,depth)
            if depth==1:
                direct.append(component)
            else:
                indirect.append(component)
            if node.file_path:
                affected_files.add(node.file_path)
            if node.node_type in {"function","method"}:
                affected_functions.add(node.name)
            if node.node_type=="class":
                affected_classes.add(node.name)
            if node.node_type=="api_endpoint":
                affected_endpoints.add(node.name)
        return ImpactAnalysis(
            target_id=node_id,
            target_name=target.name,
            direct_impact=direct,
            indirect_impact=indirect,
            affected_files=sorted(affected_files),
            affected_functions=sorted(affected_functions),
            affected_classes=sorted(affected_classes),
            affected_endpoints=sorted(affected_endpoints),
            total_affected=len(impacted),
            maximum_depth=maximum_depth
        )
    def analyze_multiple(self,node_ids:List[str],max_depth:Optional[int]=None)->Dict[str,ImpactAnalysis]:
        results={}
        for node_id in node_ids:
            if self.graph.get_node(node_id):
                results[node_id]=self.analyze(node_id,max_depth)
        return results
    def _to_component(self,node:DependencyNode,depth:int)->ImpactedComponent:
        return ImpactedComponent(
            id=node.id,
            name=node.name,
            node_type=node.node_type,
            file_path=node.file_path,
            depth=depth
        )