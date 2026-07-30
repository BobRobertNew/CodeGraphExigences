from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from .entities import Node, Edge, NodeType

class IGraphCommand(ABC):
    """Interface for operations that modify the graph."""

    @abstractmethod
    def add_node(self, node: Node, owner: str) -> None:
        """
        Adds a new node to the graph.

        Args:
            node (Node): The node to add to the graph.
            owner (str): The owner of the node.
        """
        pass

    @abstractmethod
    def add_edge(self, edge: Edge) -> None:
        """
        Adds a new edge to the graph.

        Args:
            edge (Edge): The edge to add to the graph.
        """
        pass

    @abstractmethod
    def remove_node(self, node_id: str) -> None:
        """
        Removes a node from the graph by its ID.

        Args:
            node_id (str): The unique identifier of the node to remove.
        """
        pass



    @abstractmethod
    def add_log(self, log_entry: dict) -> None:
        """
        Adds a log entry for operations performed on the graph.

        Args:
            log_entry (dict): The log entry detailing the action.
        """
        pass


class IGraphStorage(ABC):
    """Interface for operations that save and load the graph."""

    @abstractmethod
    def save_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Saves the graph to a file.

        Args:
            filepath (str): The path to the file where the graph will be saved.
            format (str): The format of the file to save (default is "graphml").
        """
        pass

    @abstractmethod
    def load_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Loads the graph from a file.

        Args:
            filepath (str): The path to the file from which to load the graph.
            format (str): The format of the file being loaded (default is "graphml").
        """
        pass


class IGraphQuery(ABC):
    """Interface for operations that query the graph."""

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Retrieves a node from the graph by its ID.

        Args:
            node_id (str): The unique identifier of the node.

        Returns:
            Optional[Node]: The node object if found, otherwise None.
        """
        pass

    @abstractmethod
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """
        Retrieves all nodes of a specific type.

        Args:
            node_type (NodeType): The type of nodes to retrieve.

        Returns:
            List[Node]: A list of nodes matching the specified type.
        """
        pass

    @abstractmethod
    def find_node_by_exact_metadata(self, key: str, value: Any, node_type: Optional[NodeType] = None) -> Optional[Node]:
        """
        Finds a single node matching a metadata key/value pair.

        Args:
            key (str): The metadata key to search for.
            value (Any): The metadata value to search for.
            node_type (Optional[NodeType]): An optional node type to filter the search.

        Returns:
            Optional[Node]: The node object if a match is found, otherwise None.
        """
        pass

    @abstractmethod
    def get_neighbors(self, node_id: str, filter_type: Optional[NodeType] = None) -> List[Node]:
        """
        Gets neighbor nodes, optionally filtering by type.

        Args:
            node_id (str): The ID of the central node.
            filter_type (Optional[NodeType]): An optional type to filter the neighboring nodes.

        Returns:
            List[Node]: A list of neighbor nodes connected to the central node.
        """
        pass

    @abstractmethod
    def has_path(self, source_id: str, target_id: str) -> bool:
        """
        Checks if a path exists between two nodes.

        Args:
            source_id (str): The ID of the starting node.
            target_id (str): The ID of the destination node.

        Returns:
            bool: True if a path exists between the two nodes, otherwise False.
        """
        pass

    @abstractmethod
    def get_all_nodes(self) -> List[Node]:
        """
        Retrieves all nodes currently in the graph.

        Returns:
            List[Node]: A list of all nodes.
        """
        pass

    @abstractmethod
    def get_all_edges(self) -> List[Edge]:
        """
        Retrieves all edges currently in the graph.

        Returns:
            List[Edge]: A list of all edges.
        """
        pass
