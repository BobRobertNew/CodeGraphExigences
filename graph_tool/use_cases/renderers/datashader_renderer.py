import os
import networkx as nx
import holoviews as hv
from holoviews.operation.datashader import datashade
from ...domain.ports import IGraphQuery
from .base import GraphRenderer

# Initialize holoviews with bokeh extension
hv.extension('bokeh')

class DatashaderRenderer(GraphRenderer):
    """
    Renders the graph using Datashader + HoloViews to handle large datasets.
    """

    def render(self, query_repo: IGraphQuery, output_file: str, **kwargs) -> str:
        """
        Generates a rasterized visualization of the graph using Datashader.

        Args:
            query_repo (IGraphQuery): The repository interface used for reading graph data.
            output_file (str): The name or path of the HTML file to generate.
            **kwargs:
                base_dir (str, optional): The base directory for saving the output. Used for path traversal protection. Defaults to current working directory.
                layout (str, optional): The networkx layout algorithm to use ('spring', 'circular', 'kamada_kawai', etc). Defaults to 'spring'.

        Returns:
            str: The absolute path to the generated HTML file.
        """
        base_dir = kwargs.get('base_dir', os.getcwd())
        layout_name = kwargs.get('layout', 'spring')

        base_dir_abs = os.path.abspath(base_dir)
        target_abs = os.path.abspath(output_file)

        try:
            if os.path.commonpath([base_dir_abs, target_abs]) != base_dir_abs:
                raise ValueError("Path traversal detected: output file is outside the allowed directory.")
        except ValueError as e:
            if "Path traversal detected" in str(e):
                raise
            raise ValueError("Invalid path provided.") from e

        # Reconstruct a basic NetworkX graph from the repository for layout algorithms
        nx_graph = nx.Graph()
        nodes = query_repo.get_all_nodes()
        edges = query_repo.get_all_edges()

        for node in nodes:
            nx_graph.add_node(node.id)
        for edge in edges:
            nx_graph.add_edge(edge.source_id, edge.target_id)

        # Apply chosen layout
        if layout_name == 'circular':
            pos = nx.circular_layout(nx_graph)
        elif layout_name == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(nx_graph)
        elif layout_name == 'random':
            pos = nx.random_layout(nx_graph)
        else:
            # Default to spring layout
            pos = nx.spring_layout(nx_graph)

        # Create holoviews Graph
        graph = hv.Graph.from_networkx(nx_graph, pos)

        # Apply datashader
        shaded = datashade(graph)

        # Save to output file
        hv.save(shaded, target_abs, fmt='html')

        return target_abs
