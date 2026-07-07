import os
from datetime import datetime
import warnings
import matplotlib.pyplot as plt
from upsetplot import from_contents, plot
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

    def generate_upset_plot(self, ensemble_type: NodeType, element_type: NodeType, output_file: str = None) -> str:
        """
        Generates an UpSet plot to show the intersections of element nodes grouped by ensemble nodes.
        For example, ensemble_type=NodeType.PROJET and element_type=NodeType.EXIGENCE will show
        the volumes of Exigences shared (or not) between Projects.

        Args:
            ensemble_type (NodeType): The type of nodes to use as the sets/ensembles.
            element_type (NodeType): The type of nodes to use as the elements inside the sets.
            output_file (str, optional): The path to save the generated image. Defaults to a horodated filename.

        Returns:
            str: The path to the saved image file.
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"upset_plot_{timestamp}.png"

        ensembles = self.qry.get_nodes_by_type(ensemble_type)
        contents = {}
        for ensemble in ensembles:
            name = ensemble.metadata.get("name") or ensemble.id
            neighbors = self.qry.get_neighbors(ensemble.id, filter_type=element_type)
            element_ids = {n.id for n in neighbors}
            if element_ids:
                contents[name] = element_ids

        if not contents:
            # Handle empty data
            warnings.warn("No data available to generate UpSet plot.")
            return output_file

        # Check if contents has at least two keys or valid set overlap.
        # upsetplot requires MultiIndex. If there's only 1 set, it fails.
        if len(contents) < 2:
            warnings.warn("UpSet plot requires at least 2 sets/ensembles.")
            return output_file

        # Ignore FutureWarnings from upsetplot/pandas
        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=FutureWarning)
            data = from_contents(contents)
            plot(data)
            plt.savefig(output_file)
            plt.close()

        return output_file
