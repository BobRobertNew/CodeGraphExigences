import os
from pyvis.network import Network
from ...domain.entities import NodeType
from ...domain.ports import IGraphQuery
from .base import GraphRenderer

class PyVisRenderer(GraphRenderer):
    """
    Renders the graph using PyVis for interactive HTML visualization.
    """

    def render(self, query_repo: IGraphQuery, output_file: str, **kwargs) -> str:
        """
        Generates an interactive HTML visualization of the current graph using pyvis.
        Includes path traversal protection.

        Args:
            query_repo (IGraphQuery): The repository interface used for reading graph data.
            output_file (str): The name or path of the HTML file to generate.
            **kwargs:
                base_dir (str, optional): The base directory for saving the output. Used for path traversal protection. Defaults to current working directory.

        Returns:
            str: The absolute path to the generated HTML file.
        """
        base_dir = kwargs.get('base_dir', os.getcwd())

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

        nodes = query_repo.get_all_nodes()
        edges = query_repo.get_all_edges()

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
