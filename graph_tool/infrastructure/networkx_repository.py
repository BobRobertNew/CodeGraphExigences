import networkx as nx
from datetime import datetime
import os
from typing import List, Optional, Any
import json
import pickle
from ..domain.entities import Node, Edge, NodeType
from ..domain.ports import IGraphCommand, IGraphQuery, IGraphStorage

class NetworkXGraphRepository(IGraphCommand, IGraphQuery, IGraphStorage):
    """
    Concrete implementation of the graph repository using NetworkX.
    Implements Command, Query, and Storage interfaces for a single underlying NetworkX graph.
    """

    def __init__(self):
        """
        Initializes an empty NetworkX graph.
        """
        self.graph = nx.Graph()
        self.logs = []

    def save_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Saves the graph to a file in the specified format.

        Args:
            filepath (str): The path to the file.
            format (str): The format to save the graph in. Supported formats are "graphml", "gexf", "json", and "pickle".

        Raises:
            ValueError: If an unsupported format is provided.
        """
        if format == "graphml":
            nx.write_graphml(self.graph, filepath)
        elif format == "gexf":
            nx.write_gexf(self.graph, filepath)
        elif format == "json":
            data = nx.node_link_data(self.graph)
            with open(filepath, 'w') as f:
                json.dump(data, f)
        elif format == "pickle":
            with open(filepath, 'wb') as f:
                pickle.dump(self.graph, f)
        else:
            raise ValueError(f"Unsupported format: {format}")


        # Save logs to a corresponding JSON file
        base_name, _ = os.path.splitext(filepath)
        log_filepath = f"{base_name}_logs.json"
        with open(log_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=4, ensure_ascii=False)

    def load_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Loads the graph from a file in the specified format.

        Args:
            filepath (str): The path to the file.
            format (str): The format to load the graph from. Supported formats are "graphml", "gexf", "json", and "pickle".

        Raises:
            ValueError: If an unsupported format is provided.
        """
        if format == "graphml":
            self.graph = nx.read_graphml(filepath)
        elif format == "gexf":
            self.graph = nx.read_gexf(filepath)
        elif format == "json":
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
        elif format == "pickle":
            with open(filepath, 'rb') as f:
                self.graph = pickle.load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")


        # Load logs if the corresponding JSON file exists
        base_name, _ = os.path.splitext(filepath)
        log_filepath = f"{base_name}_logs.json"
        if os.path.exists(log_filepath):
            with open(log_filepath, 'r', encoding='utf-8') as f:
                try:
                    self.logs = json.load(f)
                except json.JSONDecodeError:
                    self.logs = []
        else:
            self.logs = []

    def add_node(self, node: Node, owner: str) -> None:
        """
        Adds a node to the NetworkX graph.

        Args:
            node (Node): The node to add. If it already exists, nothing happens.
            owner (str): The owner of the node.
        """
        if not self.graph.has_node(node.id):
            metadata_dict = node.metadata.copy()
            metadata_dict["type"] = node.type.value
            metadata_dict["owner"] = owner
            if "status" not in metadata_dict:
                metadata_dict["status"] = "Expérimental"
            metadata_dict["creation_date"] = datetime.now().isoformat()
            self.graph.add_node(node.id, **metadata_dict)

    def add_edge(self, edge: Edge) -> None:
        """
        Adds an edge to the NetworkX graph.

        Args:
            edge (Edge): The edge to add. The source and target nodes must already exist in the graph.
        """
        if self.graph.has_node(edge.source_id) and self.graph.has_node(edge.target_id):
            self.graph.add_edge(edge.source_id, edge.target_id, type=edge.type, **edge.metadata)

    def remove_node(self, node_id: str) -> None:
        """
        Removes a node from the NetworkX graph.

        Args:
            node_id (str): The ID of the node to remove. If it does not exist, nothing happens.
        """
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Retrieves a node from the NetworkX graph.

        Args:
            node_id (str): The ID of the node to retrieve.

        Returns:
            Optional[Node]: The node object if found, otherwise None.
        """
        if self.graph.has_node(node_id):
            data = dict(self.graph.nodes[node_id])
            type_str = data.pop("type")
            return Node(id=node_id, type=NodeType(type_str), metadata=data)
        return None

    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """
        Retrieves all nodes of a specific type from the NetworkX graph.

        Args:
            node_type (NodeType): The type of nodes to retrieve.

        Returns:
            List[Node]: A list of nodes matching the specified type.
        """
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == node_type.value:
                meta = dict(data)
                meta.pop("type", None)
                nodes.append(Node(id=node_id, type=node_type, metadata=meta))
        return nodes

    def find_node_by_exact_metadata(self, key: str, value: Any, node_type: Optional[NodeType] = None) -> Optional[Node]:
        """
        Finds a single node in the NetworkX graph matching a metadata key/value pair.

        Args:
            key (str): The metadata key to search for.
            value (Any): The metadata value to search for.
            node_type (Optional[NodeType]): An optional node type to filter the search.

        Returns:
            Optional[Node]: The node object if a match is found, otherwise None.
        """
        for node_id, data in self.graph.nodes(data=True):
            if data.get(key) == value:
                if node_type and data.get("type") != node_type.value:
                    continue
                meta = dict(data)
                type_str = meta.pop("type", None)
                return Node(id=node_id, type=NodeType(type_str) if type_str else node_type, metadata=meta)
        return None

    def get_neighbors(self, node_id: str, filter_type: Optional[NodeType] = None) -> List[Node]:
        """
        Gets neighbor nodes from the NetworkX graph, optionally filtering by type.

        Args:
            node_id (str): The ID of the central node.
            filter_type (Optional[NodeType]): An optional type to filter the neighboring nodes.

        Returns:
            List[Node]: A list of neighbor nodes.
        """
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
        """
        Checks if a path exists between two nodes in the NetworkX graph.

        Args:
            source_id (str): The ID of the starting node.
            target_id (str): The ID of the destination node.

        Returns:
            bool: True if a path exists, otherwise False.
        """
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return False
        return nx.has_path(self.graph, source_id, target_id)

    def get_all_nodes(self) -> List[Node]:
        """
        Retrieves all nodes currently in the NetworkX graph.

        Returns:
            List[Node]: A list of all nodes.
        """
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            meta = dict(data)
            type_str = meta.pop("type", None)
            node_type = NodeType(type_str) if type_str else None
            nodes.append(Node(id=node_id, type=node_type, metadata=meta))
        return nodes

    def get_all_edges(self) -> List[Edge]:
        """
        Retrieves all edges currently in the NetworkX graph.

        Returns:
            List[Edge]: A list of all edges.
        """
        edges = []
        for u, v, data in self.graph.edges(data=True):
            meta = dict(data)
            type_str = meta.pop("type", "LINKED_TO")
            edges.append(Edge(source_id=u, target_id=v, type=type_str, metadata=meta))
        return edges

    def add_log(self, log_entry: dict) -> None:
        """
        Adds a log entry for operations performed on the graph.

        Args:
            log_entry (dict): The log entry detailing the action.
        """
        self.logs.append(log_entry)
