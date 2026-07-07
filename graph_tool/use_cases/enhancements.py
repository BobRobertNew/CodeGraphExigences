import os
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
from typing import List, Dict, Any, Optional
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

    def generate_venn_diagram_html(
        self,
        ensemble_type: NodeType,
        element_type: NodeType,
        target_ensembles: Optional[List[str]] = None,
        output_file: str = "venn_diagram.html"
    ) -> Optional[str]:
        """
        Generates a Venn diagram comparing the shared elements between different ensembles
        (e.g., Exigences shared between Projects) and saves it as an HTML file containing a base64 image.
        Limited to a maximum of 3 ensembles to produce a valid Venn diagram.

        Args:
            ensemble_type (NodeType): The type of node used as the ensemble (e.g., NodeType.PROJET).
            element_type (NodeType): The type of node used as the elements (e.g., NodeType.EXIGENCE).
            target_ensembles (Optional[List[str]]): List of specific ensemble node names to include.
                                                    If None, it tries to pick up to 3 available.
            output_file (str): Output HTML filename.

        Returns:
            Optional[str]: Path to the generated HTML file, or None if not enough data.
        """
        ensembles = self.qry.get_nodes_by_type(ensemble_type)

        # Filter by names if provided
        if target_ensembles:
            ensembles = [e for e in ensembles if e.metadata.get("name") in target_ensembles]

        if not ensembles:
            print("No ensembles found to generate Venn diagram.")
            return None

        if len(ensembles) > 3:
            print(f"Warning: Venn diagrams support a maximum of 3 sets. Slicing to the first 3 (from {len(ensembles)}).")
            ensembles = ensembles[:3]

        if len(ensembles) < 2:
            print("Error: Need at least 2 ensembles to generate a Venn diagram.")
            return None

        # Build sets of element IDs for each ensemble
        sets = []
        labels = []
        for ens in ensembles:
            labels.append(ens.metadata.get("name", ens.id))
            elements = self.qry.get_neighbors(ens.id, filter_type=element_type)
            sets.append(set(e.id for e in elements))

        # Generate plot
        plt.figure(figsize=(8, 8))
        if len(sets) == 2:
            venn2(sets, set_labels=labels)
        elif len(sets) == 3:
            venn3(sets, set_labels=labels)

        plt.title(f"Shared {element_type.value}s between {ensemble_type.value}s")

        # Save to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()

        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        # Generate HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Venn Diagram</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f9f9f9;
                }}
                .container {{
                    text-align: center;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>{ensemble_type.value} / {element_type.value} Venn Diagram</h2>
                <img src="data:image/png;base64,{image_base64}" alt="Venn Diagram" />
            </div>
        </body>
        </html>
        """

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_file
