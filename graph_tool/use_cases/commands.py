import warnings
import pandas as pd
from typing import Union, List, Callable
from ..domain.entities import Node, Edge, NodeType
from ..domain.ports import IGraphCommand, IGraphQuery
from ..utils.text_utils import generate_short_id, find_best_match
from ..infrastructure.data_loader import load_and_clean_data, clean_dataframe
from .extractors import IExtractionStep, LegacyExigenceExtractionStep

class CommandHandler:
    """
    Handles operations that modify the graph, adding nodes and edges.
    """

    def __init__(self, command_repo: IGraphCommand, query_repo: IGraphQuery):
        """
        Initializes the CommandHandler.

        Args:
            command_repo (IGraphCommand): The repository interface for writing to the graph.
            query_repo (IGraphQuery): The repository interface for reading from the graph.
        """
        self.cmd = command_repo
        self.qry = query_repo

    def add_project_exigences(
        self,
        project_name: str,
        data_source: Union[str, pd.DataFrame],
        loader: Callable[[Union[str, pd.DataFrame]], pd.DataFrame] = load_and_clean_data,
        steps: List[IExtractionStep] = None
    ):
        """
        Adds project requirements (exigences) to the graph.

        Args:
            project_name (str): The name of the project.
            data_source (Union[str, pd.DataFrame]): Path to the data file or a pandas DataFrame.
            loader (Callable): Function to load the data_source into a DataFrame.
            steps (List[IExtractionStep]): List of extraction steps to apply. If None, uses legacy logic.
        """
        df = loader(data_source)
        if loader != load_and_clean_data:
            df = clean_dataframe(df)

        if "Etat de Conformité" in df.columns:
            mask_contains = df["Etat de Conformité"].astype(str).str.contains("Surveillance conformité", case=False, na=False)
            mask_exact = df["Etat de Conformité"].astype(str).str.contains("Surveillance conformité", case=True, na=False)

            if (mask_contains & ~mask_exact).any():
                warnings.warn("Some rows matched 'Surveillance conformité' with different casing.")

            df = df[mask_contains].copy()
        else:
            warnings.warn("Column 'Etat de Conformité' not found. Proceeding without filtering.")

        # 1. Ensure Project Node exists
        proj_node = self.qry.find_node_by_exact_metadata("name", project_name, NodeType.PROJET)
        if not proj_node:
            proj_node = Node(id=f"PROJ-{project_name}", type=NodeType.PROJET, metadata={"name": project_name})
            self.cmd.add_node(proj_node)

        # 2. Run extraction steps
        if steps is None:
            steps = [LegacyExigenceExtractionStep()]

        for step in steps:
            step.execute(df, proj_node, self.cmd, self.qry)

    def add_rex(
        self,
        project_name: str,
        data_source: Union[str, pd.DataFrame],
        loader: Callable[[Union[str, pd.DataFrame]], pd.DataFrame] = load_and_clean_data
    ):
        """
        Creates Return on Experience (REX) nodes linked to a Project and an Exigence.

        Expected column in the data source:
        - Exigence or Exigences (used to find the existing Exigence node via exact or fuzzy description matching)
        - REX Detail or Commentaire general (used for the REX description)

        Args:
            project_name (str): The name of the project.
            data_source (Union[str, pd.DataFrame]): Path to the data file or a pandas DataFrame.
            loader (Callable): Function to load the data_source into a DataFrame.

        Raises:
            ValueError: If the project is not found in the graph or if an Exigence cannot be matched,
                        or if neither 'REX Detail' nor 'Commentaire general' column is found.
        """
        df = loader(data_source)

        if "Commentaire general" in df.columns:
            rex_col = "Commentaire general"
        elif "REX Detail" in df.columns:
            rex_col = "REX Detail"
        else:
            raise ValueError("Neither 'REX Detail' nor 'Commentaire general' column is found in the provided data source.")

        if "Exigences" in df.columns:
            exigence_col = "Exigences"
        else:
            exigence_col = "Exigence"

        proj_node = self.qry.find_node_by_exact_metadata("name", project_name, NodeType.PROJET)
        if not proj_node:
            raise ValueError(f"Project '{project_name}' not found. Please add the project first.")

        # Pre-fetch all exigence descriptions to allow fuzzy matching
        all_exigences = self.qry.get_nodes_by_type(NodeType.EXIGENCE)
        exigence_descriptions = {exg.metadata.get("description", ""): exg for exg in all_exigences}
        desc_list = list(exigence_descriptions.keys())

        for idx, row in df.iterrows():
            exigence_text = str(row.get(exigence_col, "")).strip()
            rex_detail_text = str(row.get(rex_col, "")).strip()
            if not exigence_text:
                continue

            # Try exact match first, then fuzzy
            target_exg = None
            if exigence_text in exigence_descriptions:
                target_exg = exigence_descriptions[exigence_text]
            else:
                best_match_text = find_best_match(exigence_text, desc_list)
                if best_match_text:
                    target_exg = exigence_descriptions[best_match_text]

            if not target_exg:
                raise ValueError(f"Exigence matching '{exigence_text}' not found in the graph.")

            # Create REX
            # ID codification readable
            rex_id = f"REX-{project_name}-EXG-{target_exg.id.split('-')[-1]}"
            # Ensure uniqueness if multiple REX for same exg/proj
            base_rex_id = rex_id
            counter = 1
            while self.qry.get_node(rex_id):
                rex_id = f"{base_rex_id}-{counter}"
                counter += 1

            metadata = {}
            if rex_detail_text:
                metadata["description"] = rex_detail_text

            rex_node = Node(id=rex_id, type=NodeType.REX, metadata=metadata)
            self.cmd.add_node(rex_node)

            # Link REX to Project and Exigence
            self.cmd.add_edge(Edge(rex_node.id, proj_node.id))
            self.cmd.add_edge(Edge(rex_node.id, target_exg.id))

    def add_specification(self, spec_id: str, spec_name: str, data_source: Union[str, pd.DataFrame]):
        """
        Creates a Specification node and connects it to a list of Exigence nodes.

        Expected column in the data source:
        - Exigence (text)

        Args:
            spec_id (str): The unique ID of the specification.
            spec_name (str): The name of the specification.
            data_source (Union[str, pd.DataFrame]): Path to the data file or a pandas DataFrame.
        """
        df = load_and_clean_data(data_source)

        spec_node = self.qry.get_node(spec_id)
        if not spec_node:
            spec_node = Node(id=spec_id, type=NodeType.SPECIFICATION, metadata={"name": spec_name})
            self.cmd.add_node(spec_node)

        all_exigences = self.qry.get_nodes_by_type(NodeType.EXIGENCE)
        exigence_descriptions = {exg.metadata.get("description", ""): exg for exg in all_exigences}
        desc_list = list(exigence_descriptions.keys())

        for _, row in df.iterrows():
            exigence_text = str(row.get("Exigence", "")).strip()
            if not exigence_text:
                continue

            # Try exact/fuzzy matching
            target_exg = None
            if exigence_text in exigence_descriptions:
                target_exg = exigence_descriptions[exigence_text]
            else:
                best_match_text = find_best_match(exigence_text, desc_list)
                if best_match_text:
                    target_exg = exigence_descriptions[best_match_text]

            # Create new Exigence node if it doesn't exist even after fuzzy matching
            if not target_exg:
                exg_id = generate_short_id("EXG", exigence_text)
                target_exg = Node(id=exg_id, type=NodeType.EXIGENCE, metadata={"description": exigence_text})
                self.cmd.add_node(target_exg)
                # update dict and list for subsequent rows
                exigence_descriptions[exigence_text] = target_exg
                desc_list.append(exigence_text)

            self.cmd.add_edge(Edge(spec_node.id, target_exg.id))

    def add_contract(self, contract_id: str, contract_name: str, data_source: Union[str, pd.DataFrame]):
        """
        Creates a Contract node and connects it to Document nodes.

        Expected columns in the data source:
        - Document (name)
        - Description

        Args:
            contract_id (str): The unique ID of the contract.
            contract_name (str): The name of the contract.
            data_source (Union[str, pd.DataFrame]): Path to the data file or a pandas DataFrame.
        """
        df = load_and_clean_data(data_source)

        contract_node = self.qry.get_node(contract_id)
        if not contract_node:
            contract_node = Node(id=contract_id, type=NodeType.CONTRAT, metadata={"name": contract_name})
            self.cmd.add_node(contract_node)

        for _, row in df.iterrows():
            doc_name = str(row.get("Document", "")).strip()
            doc_desc = str(row.get("Description", "")).strip()

            if not doc_name:
                continue

            # Identify Document by ID or Name
            doc_id = f"DOC-{doc_name}"
            doc_node = self.qry.get_node(doc_id)
            if not doc_node:
                doc_node = Node(id=doc_id, type=NodeType.DOCUMENT, metadata={"name": doc_name, "description": doc_desc})
                self.cmd.add_node(doc_node)

            self.cmd.add_edge(Edge(contract_node.id, doc_node.id))
