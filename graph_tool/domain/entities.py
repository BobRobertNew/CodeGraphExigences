from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

class NodeType(Enum):
    """
    Enum representing the different types of nodes available in the graph.
    """
    PROJET = "Projet"
    EXIGENCE = "Exigence"
    LOI = "Loi"
    PHASE_PROJET = "Phase projet"
    METIER = "Métier"
    REX = "REX"
    SPECIFICATION = "Spécification"
    CONTRAT = "Contrat"
    SITE = "Site"
    DOCUMENT = "Document"
    PREUVE = "Preuve de conformité"
    ARTICLE = "Article"
    SOUS_ARTICLE = "Sous Article"

@dataclass
class Node:
    """
    Represents a node in the graph.

    Attributes:
        id (str): The unique identifier of the node.
        type (NodeType): The type of the node.
        metadata (Dict[str, Any]): Additional metadata associated with the node.
    """
    id: str
    type: NodeType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        """
        Computes the hash based on the node's unique ID.
        """
        return hash(self.id)

    def __eq__(self, other):
        """
        Checks equality based on the node's unique ID.
        """
        if not isinstance(other, Node):
            return NotImplemented
        return self.id == other.id

@dataclass
class Edge:
    """
    Represents a directed edge (connection) between two nodes in the graph.

    Attributes:
        source_id (str): The unique identifier of the source node.
        target_id (str): The unique identifier of the target node.
        type (str): The type of relationship between the nodes.
        metadata (Dict[str, Any]): Additional metadata associated with the edge.
    """
    source_id: str
    target_id: str
    type: str = "LINKED_TO"
    metadata: Dict[str, Any] = field(default_factory=dict)
