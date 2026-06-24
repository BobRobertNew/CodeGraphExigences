from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from .entities import Node, Edge, NodeType

class IGraphCommand(ABC):
    """Interface for operations that modify the graph."""

    @abstractmethod
    def add_node(self, node: Node) -> None:
        pass

    @abstractmethod
    def add_edge(self, edge: Edge) -> None:
        pass

    @abstractmethod
    def remove_node(self, node_id: str) -> None:
        pass


class IGraphQuery(ABC):
    """Interface for operations that query the graph."""

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Node]:
        pass

    @abstractmethod
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        pass

    @abstractmethod
    def find_node_by_exact_metadata(self, key: str, value: Any, node_type: Optional[NodeType] = None) -> Optional[Node]:
        """Finds a single node matching a metadata key/value pair."""
        pass

    @abstractmethod
    def get_neighbors(self, node_id: str, filter_type: Optional[NodeType] = None) -> List[Node]:
        """Gets neighbor nodes, optionally filtering by type."""
        pass

    @abstractmethod
    def has_path(self, source_id: str, target_id: str) -> bool:
        """Checks if a path exists between two nodes."""
        pass

    @abstractmethod
    def get_all_nodes(self) -> List[Node]:
        pass

    @abstractmethod
    def get_all_edges(self) -> List[Edge]:
        pass
