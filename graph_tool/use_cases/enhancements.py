import os
from typing import List, Dict, Any
from ..domain.entities import NodeType
from ..domain.ports import IGraphQuery
from .renderers import GraphRenderer, PyVisRenderer

class GraphEnhancements:
    """
    Provides additional features on top of the graph, such as visualization and integrity checking.
    """

    def __init__(self, query_repo: IGraphQuery):
        """
        Initializes GraphEnhancements.

        Args:
            query_repo (IGraphQuery): The repository interface used for reading graph data.
        """
        self.qry = query_repo

    def visualize_graph(self, output_file: str = "graph_visualization.html", renderer: GraphRenderer = None, **kwargs):
        """
        Generates a visualization of the current graph using the provided rendering engine.

        Args:
            output_file (str): The name or path of the file to generate. Defaults to "graph_visualization.html".
            renderer (GraphRenderer, optional): The rendering engine to use. Defaults to PyVisRenderer if None.
            **kwargs: Additional engine-specific configuration options (e.g., base_dir, layout).

        Returns:
            Any: The absolute path to the generated visualization or engine-specific output.
        """
        if renderer is None:
            renderer = PyVisRenderer()

        return renderer.render(self.qry, output_file, **kwargs)

    def check_graph_integrity(self) -> Dict[str, List[str]]:
        """
        Checks the integrity of the graph and identifies potentially dangling or incomplete nodes.
        Specifically, it checks for:
        - Requirements (Exigences) without a Proof (Preuve).
        - Projects without any Specifications (checked transitively via Exigence).

        Returns:
            Dict[str, List[str]]: A dictionary containing lists of node IDs that failed integrity checks.
                Keys include 'exigence_without_preuve' and 'project_without_specification'.
        """
        issues = {
            "exigence_without_preuve": [],
            "project_without_specification": []
        }

        # 1. Exigences without a Preuve
        exigences = self.qry.get_nodes_by_type(NodeType.EXIGENCE)
        for exg in exigences:
            preuves = self.qry.get_neighbors(exg.id, NodeType.PREUVE)
            if not preuves:
                issues["exigence_without_preuve"].append(exg.id)

        # 2. Projects without Specifications
        projects = self.qry.get_nodes_by_type(NodeType.PROJET)
        for proj in projects:
            exg_neighbors = self.qry.get_neighbors(proj.id, NodeType.EXIGENCE)
            has_spec = False
            for exg in exg_neighbors:
                specs = self.qry.get_neighbors(exg.id, NodeType.SPECIFICATION)
                if specs:
                    has_spec = True
                    break
            if not has_spec:
                issues["project_without_specification"].append(proj.id)

        return issues
