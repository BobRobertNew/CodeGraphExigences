import pandas as pd
from abc import ABC, abstractmethod
from typing import List

from ..domain.entities import Node, Edge, NodeType
from ..domain.ports import IGraphCommand, IGraphQuery
from ..utils.text_utils import generate_short_id

class IExtractionStep(ABC):
    """
    Interface for a step in the project exigences extraction pipeline.
    """
    @abstractmethod
    def execute(self, df: pd.DataFrame, proj_node: Node, cmd: IGraphCommand, qry: IGraphQuery) -> None:
        """
        Executes the extraction step.

        Args:
            df (pd.DataFrame): The DataFrame containing the data.
            proj_node (Node): The node of the project we are adding exigences to.
            cmd (IGraphCommand): The command interface to modify the graph.
            qry (IGraphQuery): The query interface to read the graph.
        """
        pass

class LegacyExigenceExtractionStep(IExtractionStep):
    """
    The original extraction logic that expects 'Normes', 'Exigence', 'Phase projet',
    'Métier', 'Preuve de conformité' columns.
    """
    def execute(self, df: pd.DataFrame, proj_node: Node, cmd: IGraphCommand, qry: IGraphQuery) -> None:
        for _, row in df.iterrows():
            loi_name = str(row.get("Normes", "")).strip()
            exigence_text = str(row.get("Exigence", "")).strip()
            phase_name = str(row.get("Phase projet", "")).strip()
            metier_name = str(row.get("Métier", "")).strip()
            preuve_text = str(row.get("Preuve de conformité", "")).strip()

            if not exigence_text:
                continue

            # Exigence Node
            exg_id = generate_short_id("EXG", exigence_text)
            exg_node = qry.get_node(exg_id)
            if not exg_node:
                exg_node = Node(id=exg_id, type=NodeType.EXIGENCE, metadata={"description": exigence_text})
                cmd.add_node(exg_node)

            # Link Project -> Exigence
            cmd.add_edge(Edge(proj_node.id, exg_node.id))

            # Loi Node
            if loi_name:
                loi_node = qry.find_node_by_exact_metadata("name", loi_name, NodeType.LOI)
                if not loi_node:
                    loi_node = Node(id=f"LOI-{loi_name}", type=NodeType.LOI, metadata={"name": loi_name})
                    cmd.add_node(loi_node)
                # Link Exigence -> Loi
                cmd.add_edge(Edge(exg_node.id, loi_node.id))

            # Phase Projet Node
            if phase_name:
                phase_node = qry.find_node_by_exact_metadata("name", phase_name, NodeType.PHASE_PROJET)
                if not phase_node:
                    phase_node = Node(id=f"PHASE-{phase_name}", type=NodeType.PHASE_PROJET, metadata={"name": phase_name})
                    cmd.add_node(phase_node)
                cmd.add_edge(Edge(exg_node.id, phase_node.id))

            # Métier Node
            if metier_name:
                metier_node = qry.find_node_by_exact_metadata("name", metier_name, NodeType.METIER)
                if not metier_node:
                    metier_node = Node(id=f"METIER-{metier_name}", type=NodeType.METIER, metadata={"name": metier_name})
                    cmd.add_node(metier_node)
                cmd.add_edge(Edge(exg_node.id, metier_node.id))

            # Preuve de conformité Node
            if preuve_text:
                preuve_id = generate_short_id("PRV", preuve_text)
                preuve_node = qry.get_node(preuve_id)
                if not preuve_node:
                    preuve_node = Node(id=preuve_id, type=NodeType.PREUVE, metadata={"description": preuve_text})
                    cmd.add_node(preuve_node)
                cmd.add_edge(Edge(exg_node.id, preuve_node.id))


class CreateExigenceAndArticlesStep(IExtractionStep):
    """
    Extracts information from "Article", "Sous_Article", and "Exigences" columns.
    Creates Article, Sous Article, and Exigence nodes and links them appropriately.
    """
    def execute(self, df: pd.DataFrame, proj_node: Node, cmd: IGraphCommand, qry: IGraphQuery) -> None:
        for _, row in df.iterrows():
            article_name = str(row.get("Article", "")).strip()
            sous_article_name = str(row.get("Sous_Article", "")).strip()
            exigence_text = str(row.get("Exigences", "")).strip()

            if not exigence_text:
                continue

            # Exigence Node
            exg_id = generate_short_id("EXG", exigence_text)
            exg_node = qry.get_node(exg_id)
            if not exg_node:
                exg_node = Node(id=exg_id, type=NodeType.EXIGENCE, metadata={"description": exigence_text})
                cmd.add_node(exg_node)

            # Link Project -> Exigence
            cmd.add_edge(Edge(proj_node.id, exg_node.id))

            current_parent = None

            # Article Node
            if article_name and article_name.lower() != "nan":
                art_id = generate_short_id("ART", article_name)
                art_node = qry.get_node(art_id)
                if not art_node:
                    art_node = Node(id=art_id, type=NodeType.ARTICLE, metadata={"name": article_name})
                    cmd.add_node(art_node)
                current_parent = art_node

            # Sous Article Node
            if sous_article_name and sous_article_name.lower() != "nan":
                sous_art_id = generate_short_id("SART", sous_article_name)
                sous_art_node = qry.get_node(sous_art_id)
                if not sous_art_node:
                    sous_art_node = Node(id=sous_art_id, type=NodeType.SOUS_ARTICLE, metadata={"name": sous_article_name})
                    cmd.add_node(sous_art_node)

                if current_parent:
                    # Link Article -> Sous Article
                    cmd.add_edge(Edge(current_parent.id, sous_art_node.id))

                current_parent = sous_art_node

            if current_parent:
                # Link Exigence to Article/Sous Article
                cmd.add_edge(Edge(exg_node.id, current_parent.id))


class LinkMetierStep(IExtractionStep):
    """
    Extracts "Métier" nodes from columns ending with "_Concerné".
    For each métier, links it to Exigences if the corresponding column contains "X".
    """
    def execute(self, df: pd.DataFrame, proj_node: Node, cmd: IGraphCommand, qry: IGraphQuery) -> None:
        metier_cols = [col for col in df.columns if str(col).endswith("_Concerné")]

        for col in metier_cols:
            metier_name = str(col).replace("_Concerné", "").strip()
            if not metier_name:
                continue

            metier_node = qry.find_node_by_exact_metadata("name", metier_name, NodeType.METIER)
            if not metier_node:
                metier_node = Node(id=f"METIER-{metier_name}", type=NodeType.METIER, metadata={"name": metier_name})
                cmd.add_node(metier_node)

            # Iterate through the DataFrame to find "X" in this column
            for _, row in df.iterrows():
                val = str(row.get(col, "")).strip().upper()
                if val == "X":
                    exigence_text = str(row.get("Exigences", "")).strip()
                    if exigence_text:
                        exg_id = generate_short_id("EXG", exigence_text)
                        exg_node = qry.get_node(exg_id)
                        if exg_node:
                            # Link Exigence -> Métier
                            cmd.add_edge(Edge(exg_node.id, metier_node.id))


class LinkPhaseProjetStep(IExtractionStep):
    """
    Links Exigences to "Phase projet".
    The possible phases are: "Conception", "Exploitation", "Commun", "Phase Etude", "Phase Contrat", "Phase Réalisation".
    If the column exists and contains an "X", links the Exigence to the corresponding Phase projet.
    """
    def execute(self, df: pd.DataFrame, proj_node: Node, cmd: IGraphCommand, qry: IGraphQuery) -> None:
        possible_phases = ["Conception", "Exploitation", "Commun", "Phase Etude", "Phase Contrat", "Phase Réalisation"]

        for phase_name in possible_phases:
            if phase_name in df.columns:
                phase_node = qry.find_node_by_exact_metadata("name", phase_name, NodeType.PHASE_PROJET)
                if not phase_node:
                    phase_node = Node(id=f"PHASE-{phase_name}", type=NodeType.PHASE_PROJET, metadata={"name": phase_name})
                    cmd.add_node(phase_node)

                for _, row in df.iterrows():
                    val = str(row.get(phase_name, "")).strip().upper()
                    if val == "X":
                        exigence_text = str(row.get("Exigences", "")).strip()
                        if exigence_text:
                            exg_id = generate_short_id("EXG", exigence_text)
                            exg_node = qry.get_node(exg_id)
                            if exg_node:
                                # Link Exigence -> Phase projet
                                cmd.add_edge(Edge(exg_node.id, phase_node.id))
