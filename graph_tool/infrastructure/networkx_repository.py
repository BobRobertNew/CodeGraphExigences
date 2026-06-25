import networkx as nx
from typing import List, Optional, Any
import json
import pickle
from ..domain.entities import Node, Edge, NodeType
from ..domain.ports import IGraphCommand, IGraphQuery, IGraphStorage

class NetworkXGraphRepository(IGraphCommand, IGraphQuery, IGraphStorage):
    def __init__(self):
        self.graph = nx.Graph()

    def save_graph(self, filepath: str, format: str = "graphml") -> None:
        if format == "graphml":
            nx.write_graphml(self.graph, filepath)
        elif format == "json":
            data = nx.node_link_data(self.graph)
            with open(filepath, 'w') as f:
                json.dump(data, f)
        elif format == "pickle":
            with open(filepath, 'wb') as f:
                pickle.dump(self.graph, f)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def load_graph(self, filepath: str, format: str = "graphml") -> None:
        if format == "graphml":
            self.graph = nx.read_graphml(filepath)
        elif format == "json":
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
        elif format == "pickle":
            with open(filepath, 'rb') as f:
                self.graph = pickle.load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def add_node(self, node: Node) -> None:
        if not self.graph.has_node(node.id):
            metadata_dict = node.metadata.copy()
            metadata_dict["type"] = node.type.value
            self.graph.add_node(node.id, **metadata_dict)

    def add_edge(self, edge: Edge) -> None:
        if self.graph.has_node(edge.source_id) and self.graph.has_node(edge.target_id):
            self.graph.add_edge(edge.source_id, edge.target_id, type=edge.type, **edge.metadata)

    def remove_node(self, node_id: str) -> None:
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)

    def get_node(self, node_id: str) -> Optional[Node]:
        if self.graph.has_node(node_id):
            data = dict(self.graph.nodes[node_id])
            type_str = data.pop("type")
            return Node(id=node_id, type=NodeType(type_str), metadata=data)
        return None

    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == node_type.value:
                meta = dict(data)
                meta.pop("type", None)
                nodes.append(Node(id=node_id, type=node_type, metadata=meta))
        return nodes

    def find_node_by_exact_metadata(self, key: str, value: Any, node_type: Optional[NodeType] = None) -> Optional[Node]:
        for node_id, data in self.graph.nodes(data=True):
            if data.get(key) == value:
                if node_type and data.get("type") != node_type.value:
                    continue
                meta = dict(data)
                type_str = meta.pop("type", None)
                return Node(id=node_id, type=NodeType(type_str) if type_str else node_type, metadata=meta)
        return None

    def get_neighbors(self, node_id: str, filter_type: Optional[NodeType] = None) -> List[Node]:
        if not self.graph.has_node(node_id):
            return []

        neighbors = []
        for neighbor_id in self.graph.neighbors(node_id):
            data = dict(self.graph.nodes[neighbor_id])
            n_type_str = data.get("type")
            n_type = NodeType(n_type_str) if n_type_str else None

            if filter_type and n_type != filter_type:
                continue

            meta = dict(data)
            meta.pop("type", None)
            neighbors.append(Node(id=neighbor_id, type=n_type, metadata=meta))
        return neighbors

    def has_path(self, source_id: str, target_id: str) -> bool:
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return False
        return nx.has_path(self.graph, source_id, target_id)

    def get_all_nodes(self) -> List[Node]:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            meta = dict(data)
            type_str = meta.pop("type", None)
            node_type = NodeType(type_str) if type_str else None
            nodes.append(Node(id=node_id, type=node_type, metadata=meta))
        return nodes

    def get_all_edges(self) -> List[Edge]:
        edges = []
        for u, v, data in self.graph.edges(data=True):
            meta = dict(data)
            type_str = meta.pop("type", "LINKED_TO")
            edges.append(Edge(source_id=u, target_id=v, type=type_str, metadata=meta))
        return edges
