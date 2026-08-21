from dataclasses import dataclass,field
from typing import List,Set
from app.graph.dependency_graph import DependencyGraph
@dataclass
class DependencyCycle:
    nodes:List[str]
    size:int
    edge_types:List[str]=field(default_factory=list)
@dataclass
class CycleAnalysisResult:
    cycles:List[DependencyCycle]=field(default_factory=list)
    cycle_count:int=0
    affected_nodes:Set[str]=field(default_factory=set)
class CycleAnalyzer:
    def analyze(self,graph:DependencyGraph)->CycleAnalysisResult:
        cycles=[]
        affected_nodes=set()
        visited=set()
        stack=[]
        on_stack=set()
        discovered=set()
        for node_id in graph.nodes:
            if node_id not in visited:
                self._dfs(
                    graph,
                    node_id,
                    visited,
                    stack,
                    on_stack,
                    discovered,
                    cycles,
                    affected_nodes
                )
        return CycleAnalysisResult(
            cycles=cycles,
            cycle_count=len(cycles),
            affected_nodes=affected_nodes
        )
    def cycles_for_node(self,graph:DependencyGraph,node_id:str)->List[DependencyCycle]:
        result=self.analyze(graph)
        return [
            cycle
            for cycle in result.cycles
            if node_id in cycle.nodes
        ]
    def _dfs(self,graph:DependencyGraph,current:str,visited:Set[str],stack:List[str],on_stack:Set[str],discovered:Set[str],cycles:List[DependencyCycle],affected_nodes:Set[str])->None:
        visited.add(current)
        stack.append(current)
        on_stack.add(current)
        for edge in graph.outgoing.get(current,[]):
            if edge.edge_type not in {"calls","imports"}:
                continue
            target=edge.target
            if target not in visited:
                self._dfs(
                    graph,
                    target,
                    visited,
                    stack,
                    on_stack,
                    discovered,
                    cycles,
                    affected_nodes
                )
            elif target in on_stack:
                try:
                    start_index=stack.index(target)
                except ValueError:
                    continue
                cycle_nodes=stack[start_index:]+[target]
                normalized=self._normalize_cycle(cycle_nodes)
                cycle_key="|".join(normalized)
                if cycle_key in discovered:
                    continue
                discovered.add(cycle_key)
                edge_types=self._edge_types(graph,normalized)
                cycles.append(
                    DependencyCycle(
                        nodes=normalized,
                        size=len(normalized)-1,
                        edge_types=edge_types
                    )
                )
                affected_nodes.update(normalized[:-1])
        stack.pop()
        on_stack.remove(current)
    def _normalize_cycle(self,nodes:List[str])->List[str]:
        core=nodes[:-1]
        if not core:
            return nodes
        rotations=[]
        for index in range(len(core)):
            rotated=core[index:]+core[:index]
            rotations.append(rotated)
        smallest=min(rotations)
        return smallest+[smallest[0]]
    def _edge_types(self,graph:DependencyGraph,nodes:List[str])->List[str]:
        types=[]
        for index in range(len(nodes)-1):
            source=nodes[index]
            target=nodes[index+1]
            for edge in graph.outgoing.get(source,[]):
                if edge.target==target:
                    types.append(edge.edge_type)
                    break
        return types