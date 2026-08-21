from typing import List
from app.analyzers.api_route_analyzer import ApiRoute
from app.graph.dependency_graph import DependencyGraph,DependencyNode
class ApiGraphIntegrator:
    def integrate(self,graph:DependencyGraph,routes:List[ApiRoute])->DependencyGraph:
        for route in routes:
            endpoint_id=self._endpoint_node_id(route)
            handler_id=f"symbol:{route.qualified_handler}"
            graph.add_node(
                DependencyNode(
                    id=endpoint_id,
                    name=f"{route.method} {route.path}",
                    node_type="api_endpoint",
                    file_path=route.file_path,
                    metadata={
                        "framework":route.framework,
                        "method":route.method,
                        "path":route.path,
                        "handler":route.qualified_handler,
                        "line":str(route.line)
                    }
                )
            )
            if handler_id in graph.nodes:
                graph.add_edge(
                    source=endpoint_id,
                    target=handler_id,
                    edge_type="routes_to",
                    confidence="confirmed"
                )
        return graph
    def _endpoint_node_id(self,route:ApiRoute)->str:
        return f"api:{route.method}:{route.path}:{route.qualified_handler}"