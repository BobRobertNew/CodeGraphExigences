import pandas as pd
from typing import List, Dict, Any, Union, Set, Tuple
from ..domain.entities import Node, NodeType
from ..domain.ports import IGraphQuery
from ..utils.text_utils import generate_short_id, find_best_match
from ..infrastructure.data_loader import load_data, clean_dataframe

class QueryHandler:
    def __init__(self, query_repo: IGraphQuery):
        self.qry = query_repo

    def _get_exigence_nodes_from_texts(self, texts: List[str]) -> List[Node]:
        """Helper to map a list of text to existing Exigence nodes using exact/fuzzy match."""
        all_exigences = self.qry.get_nodes_by_type(NodeType.EXIGENCE)
        exigence_descriptions = {exg.metadata.get("description", ""): exg for exg in all_exigences}
        desc_list = list(exigence_descriptions.keys())

        matched_nodes = []
        for text in texts:
            if not text:
                continue
            if text in exigence_descriptions:
                matched_nodes.append(exigence_descriptions[text])
            else:
                best_match = find_best_match(text, desc_list)
                if best_match:
                    matched_nodes.append(exigence_descriptions[best_match])
        return list(set(matched_nodes)) # deduplicate

    def find_most_similar_projects(self, target_project_name: str, exigencies_texts: List[str], top_k: int = 1) -> List[str]:
        """
        Given a project name and a list of exigencies text, finds the `top_k` projects
        that share the most exigencies with the provided list.
        Excludes the target_project_name from the results.
        """
        target_exigence_nodes = self._get_exigence_nodes_from_texts(exigencies_texts)
        target_exigence_ids = {node.id for node in target_exigence_nodes}

        project_nodes = self.qry.get_nodes_by_type(NodeType.PROJET)
        project_scores = {}

        for proj in project_nodes:
            if proj.metadata.get("name") == target_project_name:
                continue

            # Find all exigencies linked to this project
            proj_neighbors = self.qry.get_neighbors(proj.id, NodeType.EXIGENCE)
            proj_exg_ids = {n.id for n in proj_neighbors}

            common_count = len(target_exigence_ids.intersection(proj_exg_ids))
            if common_count > 0:
                project_scores[proj.metadata.get("name")] = common_count

        sorted_projects = sorted(project_scores.items(), key=lambda item: item[1], reverse=True)
        return [proj_name for proj_name, _ in sorted_projects[:top_k]]

    def get_useful_rex(self, project_name: str, exigencies_texts: List[str]) -> List[str]:
        """
        Given a project name and a list of exigencies text, extracts related REX nodes
        from the 2 or 3 most similar projects.
        Only extracts REX that are associated with the provided exigencies.
        """
        similar_projects = self.find_most_similar_projects(project_name, exigencies_texts, top_k=3)
        useful_rex = set()

        target_exg_nodes = self._get_exigence_nodes_from_texts(exigencies_texts)
        target_exg_ids = {n.id for n in target_exg_nodes}

        for proj_name in similar_projects:
            proj_node = self.qry.find_node_by_exact_metadata("name", proj_name, NodeType.PROJET)
            if not proj_node:
                continue

            # REX are connected to the project and to the exigence
            rex_nodes = self.qry.get_neighbors(proj_node.id, NodeType.REX)
            for rex in rex_nodes:
                # Check if this REX is connected to one of the target exigencies
                rex_exigences = self.qry.get_neighbors(rex.id, NodeType.EXIGENCE)
                if any(exg.id in target_exg_ids for exg in rex_exigences):
                    useful_rex.add(rex.id)

        return list(useful_rex)

    def complete_excel_with_graph_info(self, data_source: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Takes an excel/dataframe with an 'Exigence' column. Searches graph, and adds
        'Phase projet', 'Métier', 'Preuve de conformité' columns.
        """
        df = load_data(data_source)
        df_clean = clean_dataframe(df)

        phases_list = []
        metiers_list = []
        preuves_list = []

        for _, row in df_clean.iterrows():
            exigence_text = str(row.get("Exigence", "")).strip()
            if not exigence_text:
                phases_list.append("")
                metiers_list.append("")
                preuves_list.append("")
                continue

            nodes = self._get_exigence_nodes_from_texts([exigence_text])
            if not nodes:
                phases_list.append("")
                metiers_list.append("")
                preuves_list.append("")
                continue

            exg_node = nodes[0]
            neighbors = self.qry.get_neighbors(exg_node.id)

            phases = [n.metadata.get("name", "") for n in neighbors if n.type == NodeType.PHASE_PROJET]
            metiers = [n.metadata.get("name", "") for n in neighbors if n.type == NodeType.METIER]
            preuves = [n.metadata.get("description", "") for n in neighbors if n.type == NodeType.PREUVE]

            phases_list.append(", ".join(phases))
            metiers_list.append(", ".join(metiers))
            preuves_list.append(", ".join(preuves))

        df["Phase projet (Graph)"] = phases_list
        df["Métier (Graph)"] = metiers_list
        df["Preuve de conformité (Graph)"] = preuves_list

        return df

    def _get_spec_contract_exigences(self, spec_ids: List[str], contract_ids: List[str]) -> List[Tuple[Node, bool]]:
        """
        Helper returning a list of tuples: (Exigence Node, boolean indicating if its Preuve is linked to given contracts)
        Strict traversal: Exigence -> Preuve -> Document -> Contrat
        """
        result = []
        target_contract_ids = set(contract_ids)

        for s_id in spec_ids:
            exigences = self.qry.get_neighbors(s_id, NodeType.EXIGENCE)
            for exg in exigences:
                preuves = self.qry.get_neighbors(exg.id, NodeType.PREUVE)

                is_linked_to_contract = False
                for p in preuves:
                    documents = self.qry.get_neighbors(p.id, NodeType.DOCUMENT)
                    for d in documents:
                        contracts = self.qry.get_neighbors(d.id, NodeType.CONTRAT)
                        for c in contracts:
                            if c.id in target_contract_ids:
                                is_linked_to_contract = True
                                break
                        if is_linked_to_contract:
                            break
                    if is_linked_to_contract:
                        break

                result.append((exg, is_linked_to_contract))
        return result

    def get_exigencies_by_specs_and_contracts_linked(self, spec_ids: List[str], contract_ids: List[str]) -> List[str]:
        """Returns Exigence descriptions connected to specs AND whose Preuves are linked to the contracts."""
        data = self._get_spec_contract_exigences(spec_ids, contract_ids)
        return list({exg.metadata.get("description", "") for exg, is_linked in data if is_linked})

    def get_exigencies_by_specs_and_contracts_not_linked(self, spec_ids: List[str], contract_ids: List[str]) -> List[str]:
        """Returns Exigence descriptions connected to specs AND whose Preuves are NOT linked to the contracts."""
        data = self._get_spec_contract_exigences(spec_ids, contract_ids)
        return list({exg.metadata.get("description", "") for exg, is_linked in data if not is_linked})

    def get_exigencies_linked_to_multiple_specs(self, spec_ids: List[str]) -> List[str]:
        """Returns exigencies that are connected to AT LEAST TWO different specifications."""
        exigence_spec_count = {}
        for s_id in spec_ids:
            exigences = self.qry.get_neighbors(s_id, NodeType.EXIGENCE)
            for exg in exigences:
                exigence_spec_count[exg.id] = exigence_spec_count.get(exg.id, 0) + 1

        multi_spec_exgs = [exg_id for exg_id, count in exigence_spec_count.items() if count >= 2]
        return [self.qry.get_node(e_id).metadata.get("description", "") for e_id in multi_spec_exgs]

    def get_specifications_for_project(self, project_name: str) -> List[str]:
        """Given a project name, returns the list of specification names related to it."""
        proj_node = self.qry.find_node_by_exact_metadata("name", project_name, NodeType.PROJET)
        if not proj_node:
            return []

        # Project -> Exigence <- Specification
        exigences = self.qry.get_neighbors(proj_node.id, NodeType.EXIGENCE)
        spec_names = set()
        for exg in exigences:
            specs = self.qry.get_neighbors(exg.id, NodeType.SPECIFICATION)
            for s in specs:
                spec_names.add(s.metadata.get("name", ""))
        return list(spec_names)

    def get_contracts_for_project(self, project_name: str) -> List[str]:
        """
        Given a project name, returns the list of contract names related to it.
        Relation: Project -> Exigence -> Preuve -> Document -> Contract.
        Strict traversal to avoid merging via shared nodes (like Loi).
        """
        proj_node = self.qry.find_node_by_exact_metadata("name", project_name, NodeType.PROJET)
        if not proj_node:
            return []

        linked_contract_names = set()
        exigences = self.qry.get_neighbors(proj_node.id, NodeType.EXIGENCE)
        for exg in exigences:
            preuves = self.qry.get_neighbors(exg.id, NodeType.PREUVE)
            for p in preuves:
                documents = self.qry.get_neighbors(p.id, NodeType.DOCUMENT)
                for d in documents:
                    contracts = self.qry.get_neighbors(d.id, NodeType.CONTRAT)
                    for c in contracts:
                        linked_contract_names.add(c.metadata.get("name", ""))

        return list(linked_contract_names)

    def get_lois_from_preuves(self, preuve_texts: List[str]) -> List[str]:
        """
        From a list of Preuve texts, returns the list of Loi names related.
        Preuve -> Exigence -> Loi.
        """
        all_preuves = self.qry.get_nodes_by_type(NodeType.PREUVE)
        preuve_descriptions = {p.metadata.get("description", ""): p for p in all_preuves}

        target_preuves = []
        for text in preuve_texts:
            if text in preuve_descriptions:
                target_preuves.append(preuve_descriptions[text])
            else:
                best = find_best_match(text, list(preuve_descriptions.keys()))
                if best:
                    target_preuves.append(preuve_descriptions[best])

        loi_names = set()
        for p in target_preuves:
            exigences = self.qry.get_neighbors(p.id, NodeType.EXIGENCE)
            for exg in exigences:
                lois = self.qry.get_neighbors(exg.id, NodeType.LOI)
                for l in lois:
                    loi_names.add(l.metadata.get("name", ""))

        return list(loi_names)
