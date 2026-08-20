from dataclasses import dataclass,field
from typing import Dict,List,Optional,Set,Tuple
@dataclass
class DependencyNode:
    id:str
    name:str
    node_type:str
    file_path:str
    metadata:Dict[str,str]=field(default_factory=dict)
@dataclass
class DependencyEdge:
    source:str
    target:str
    edge_type:str
    confidence:str="confirmed"
class DependencyGraph:
    def __init__(self):
        self.nodes:Dict[str,DependencyNode]={}
        self.outgoing:Dict[str,List[DependencyEdge]]={}
        self.incoming:Dict[str,List[DependencyEdge]]={}
    def add_node(self,node:DependencyNode)->None:
        self.nodes[node.id]=node
        self.outgoing.setdefault(node.id,[])
        self.incoming.setdefault(node.id,[])
    def add_edge(self,source:str,target:str,edge_type:str,confidence:str="confirmed")->None:
        if source not in self.nodes:
            raise ValueError(f"Source node does not exist: {source}")
        if target not in self.nodes:
            raise ValueError(f"Target node does not exist: {target}")
        if self._edge_exists(source,target,edge_type):
            return
        edge=DependencyEdge(source=source,target=target,edge_type=edge_type,confidence=confidence)
        self.outgoing[source].append(edge)
        self.incoming[target].append(edge)
    def get_node(self,node_id:str)->Optional[DependencyNode]:
        return self.nodes.get(node_id)
    def get_dependencies(self,node_id:str)->List[DependencyNode]:
        edges=self.outgoing.get(node_id,[])
        return [self.nodes[edge.target] for edge in edges if edge.target in self.nodes]
    def get_dependents(self,node_id:str)->List[DependencyNode]:
        edges=self.incoming.get(node_id,[])
        return [self.nodes[edge.source] for edge in edges if edge.source in self.nodes]
    def get_direct_impact(self,node_id:str,allowed_edge_types:Optional[Set[str]]=None)->List[DependencyNode]:
        if allowed_edge_types is None:
            allowed_edge_types={"calls","imports"}
        edges=self.incoming.get(node_id,[])
        return [
            self.nodes[edge.source]
            for edge in edges
            if edge.source in self.nodes and edge.edge_type in allowed_edge_types
        ]
    def get_transitive_impact(self,node_id:str,max_depth:Optional[int]=None,allowed_edge_types:Optional[Set[str]]=None)->List[Tuple[DependencyNode,int]]:
        if node_id not in self.nodes:
            return []
        if allowed_edge_types is None:
            allowed_edge_types={"calls","imports"}
        visited:Set[str]={node_id}
        queue:List[Tuple[str,int]]=[(node_id,0)]
        impacted:List[Tuple[DependencyNode,int]]=[]
        while queue:
            current,depth=queue.pop(0)
            if max_depth is not None and depth>=max_depth:
                continue
            for edge in self.incoming.get(current,[]):
                if edge.edge_type not in allowed_edge_types:
                    continue
                dependent=edge.source
                if dependent in visited:
                    continue
                visited.add(dependent)
                next_depth=depth+1
                impacted.append((self.nodes[dependent],next_depth))
                queue.append((dependent,next_depth))
        return impacted
    def find_path(self,source:str,target:str)->List[str]:
        if source not in self.nodes or target not in self.nodes:
            return []
        queue:List[Tuple[str,List[str]]]=[(source,[source])]
        visited:Set[str]=set()
        while queue:
            current,path=queue.pop(0)
            if current==target:
                return path
            if current in visited:
                continue
            visited.add(current)
            for edge in self.outgoing.get(current,[]):
                if edge.target not in visited:
                    queue.append((edge.target,path+[edge.target]))
        return []
    def get_edges(self)->List[DependencyEdge]:
        edges=[]
        for values in self.outgoing.values():
            edges.extend(values)
        return edges
    def stats(self)->Dict[str,int]:
        return {
            "nodes":len(self.nodes),
            "edges":len(self.get_edges())
        }
    def _edge_exists(self,source:str,target:str,edge_type:str)->bool:
        return any(
            edge.target==target and edge.edge_type==edge_type
            for edge in self.outgoing.get(source,[])
        )