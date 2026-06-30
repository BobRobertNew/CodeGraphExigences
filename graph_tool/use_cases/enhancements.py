import os
from pyvis.network import Network
from typing import List, Dict, Any
from ..domain.entities import NodeType
from ..domain.ports import IGraphQuery

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

    def visualize_graph(self, output_file: str = "graph_visualization.html", base_dir: str = None):
        """
        Generates an interactive HTML visualization of the current graph using pyvis.
        Includes path traversal protection to ensure files are saved in allowed directories.

        Args:
            output_file (str): The name or path of the HTML file to generate. Defaults to "graph_visualization.html".
            base_dir (str, optional): The base directory for saving the output. Used for path traversal protection. Defaults to current working directory.

        Returns:
            str: The absolute path to the generated HTML file.

        Raises:
            ValueError: If a path traversal attempt is detected or if an invalid path is provided.
        """
        if base_dir is None:
            base_dir = os.getcwd()

        base_dir_abs = os.path.abspath(base_dir)
        target_abs = os.path.abspath(output_file)

        try:
            if os.path.commonpath([base_dir_abs, target_abs]) != base_dir_abs:
                raise ValueError("Path traversal detected: output file is outside the allowed directory.")
        except ValueError as e:
            if "Path traversal detected" in str(e):
                raise
            # If commonpath raises ValueError (e.g. on different drives in Windows)
            raise ValueError("Invalid path provided.") from e

        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=False)

        # Color mapping for different node types
        color_map = {
            NodeType.PROJET: "#FF5733",
            NodeType.EXIGENCE: "#33FF57",
            NodeType.LOI: "#3357FF",
            NodeType.PHASE_PROJET: "#F333FF",
            NodeType.METIER: "#33FFF3",
            NodeType.REX: "#FFF333",
            NodeType.SPECIFICATION: "#FF8C33",
            NodeType.CONTRAT: "#8C33FF",
            NodeType.DOCUMENT: "#8CFF33",
            NodeType.PREUVE: "#FF338C"
        }

        nodes = self.qry.get_all_nodes()
        edges = self.qry.get_all_edges()

        for node in nodes:
            label = node.metadata.get("name") or node.metadata.get("description") or node.id
            if len(label) > 20:
                label = label[:17] + "..."

            color = color_map.get(node.type, "#FFFFFF")
            title = f"Type: {node.type.value}<br>ID: {node.id}<br>"
            for k, v in node.metadata.items():
                title += f"{k}: {v}<br>"

            net.add_node(node.id, label=label, title=title, color=color)

        for edge in edges:
            net.add_edge(edge.source_id, edge.target_id, title=edge.type)

        net.save_graph(target_abs)
        return target_abs

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
