from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

class NodeType(Enum):
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

@dataclass
class Node:
    id: str
    type: NodeType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.id == other.id

@dataclass
class Edge:
    source_id: str
    target_id: str
    type: str = "LINKED_TO"
    metadata: Dict[str, Any] = field(default_factory=dict)
