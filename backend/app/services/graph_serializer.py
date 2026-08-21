from dataclasses import dataclass,field
from typing import Any
from app.graph.dependency_graph import DependencyGraph
@dataclass
class GraphNodeData:
    id:str
    name:str
    node_type:str
    file_path:str
    direct_dependents:int
    direct_dependencies:int
@dataclass
class GraphEdgeData:
    id:str
    source:str
    target:str
    edge_type:str
@dataclass
class GraphSnapshot:
    nodes:list[dict[str,Any]]=field(default_factory=list)
    edges:list[dict[str,Any]]=field(default_factory=list)
class GraphSerializer:
    def serialize(self,graph:DependencyGraph)->GraphSnapshot:
        nodes=[]
        edges=[]
        seen_edges=set()
        for node_id,node in graph.nodes.items():
            nodes.append({
                "id":node_id,
                "name":node.name,
                "node_type":node.node_type,
                "file_path":node.file_path,
                "direct_dependents":len(graph.incoming.get(node_id,[])),
                "direct_dependencies":len(graph.outgoing.get(node_id,[]))
            })
        for source_id,source_edges in graph.outgoing.items():
            for index,edge in enumerate(source_edges):
                edge_key=(source_id,edge.target,edge.edge_type)
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                edges.append({
                    "id":f"{source_id}->{edge.target}:{edge.edge_type}:{index}",
                    "source":source_id,
                    "target":edge.target,
                    "edge_type":edge.edge_type
                })
        return GraphSnapshot(
            nodes=nodes,
            edges=edges
        )
    def blast_radius(self,graph:DependencyGraph,node_id:str,max_depth:int=5)->GraphSnapshot:
        if node_id not in graph.nodes:
            return GraphSnapshot()
        included={node_id}
        impacted=graph.get_transitive_impact(node_id,max_depth=max_depth)
        for node,_ in impacted:
            node_identifier=self._node_id(graph,node)
            if node_identifier:
                included.add(node_identifier)
        nodes=[]
        edges=[]
        seen_edges=set()
        for current_id in included:
            node=graph.get_node(current_id)
            if not node:
                continue
            nodes.append({
                "id":current_id,
                "name":node.name,
                "node_type":node.node_type,
                "file_path":node.file_path,
                "direct_dependents":len(graph.incoming.get(current_id,[])),
                "direct_dependencies":len(graph.outgoing.get(current_id,[])),
                "is_target":current_id==node_id
            })
        for source_id in included:
            for index,edge in enumerate(graph.outgoing.get(source_id,[])):
                if edge.target not in included:
                    continue
                edge_key=(source_id,edge.target,edge.edge_type)
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                edges.append({
                    "id":f"{source_id}->{edge.target}:{edge.edge_type}:{index}",
                    "source":source_id,
                    "target":edge.target,
                    "edge_type":edge.edge_type
                })
        return GraphSnapshot(
            nodes=nodes,
            edges=edges
        )
    def _node_id(self,graph:DependencyGraph,target_node):
        for node_id,node in graph.nodes.items():
            if node is target_node:
                return node_id
        return None