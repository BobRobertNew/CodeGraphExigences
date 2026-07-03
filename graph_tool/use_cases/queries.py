import pandas as pd
from typing import List, Dict, Any, Union, Set, Tuple, Optional
from ..domain.entities import Node, NodeType
from ..domain.ports import IGraphQuery
from ..utils.text_utils import generate_short_id, find_best_match
from ..infrastructure.data_loader import load_and_clean_data

class QueryHandler:
    """
    Handles graph querying operations, extracting insights from the graph data.
    """

    def __init__(self, query_repo: IGraphQuery):
        """
        Initializes the QueryHandler.

        Args:
            query_repo (IGraphQuery): The repository interface for reading from the graph.
        """
        self.qry = query_repo

    def _get_exigence_nodes_from_texts(self, texts: List[str], exact_match: bool = False) -> List[Node]:
        """
        Helper method to map a list of requirement texts to existing Exigence nodes
        using exact or fuzzy matching.

        Args:
            texts (List[str]): List of requirement texts to match.
            exact_match (bool): If True, skips fuzzy matching. Defaults to False.

        Returns:
            List[Node]: A deduplicated list of matching Exigence nodes.
        """
        all_exigences = self.qry.get_nodes_by_type(NodeType.EXIGENCE)
        exigence_descriptions = {exg.metadata.get("description", ""): exg for exg in all_exigences}
        desc_list = list(exigence_descriptions.keys())

        matched_nodes = []
        for text in texts:
            if not text:
                continue
            if text in exigence_descriptions:
                matched_nodes.append(exigence_descriptions[text])
            elif not exact_match:
                best_match = find_best_match(text, desc_list)
                if best_match:
                    matched_nodes.append(exigence_descriptions[best_match])
        return list(set(matched_nodes)) # deduplicate

    def find_most_similar_projects(self, target_project_name: str, exigencies_texts: List[str], top_k: int = 1, exact_match: bool = False) -> List[str]:
        """
        Given a project name and a list of exigencies text, finds the `top_k` projects
        that share the most exigencies with the provided list.
        Excludes the target project from the results.

        Args:
            target_project_name (str): The name of the baseline project to exclude.
            exigencies_texts (List[str]): A list of requirement texts to compare against.
            top_k (int): The maximum number of similar projects to return. Defaults to 1.
            exact_match (bool): If True, skips fuzzy matching. Defaults to False.

        Returns:
            List[str]: A list containing the names of the most similar projects.
        """
        target_exigence_nodes = self._get_exigence_nodes_from_texts(exigencies_texts, exact_match=exact_match)
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

    def get_useful_rex(self, project_name: str, exigencies_texts: List[str], exact_match: bool = False) -> List[str]:
        """
        Given a project name and a list of exigencies text, extracts related REX (Return on Experience)
        nodes from the up to 3 most similar projects.
        Only extracts REX that are associated with the provided exigencies.

        Args:
            project_name (str): The name of the baseline project.
            exigencies_texts (List[str]): A list of requirement texts.
            exact_match (bool): If True, skips fuzzy matching. Defaults to False.

        Returns:
            List[str]: A list of IDs for the useful REX nodes.
        """
        similar_projects = self.find_most_similar_projects(project_name, exigencies_texts, top_k=3, exact_match=exact_match)
        useful_rex = set()

        target_exg_nodes = self._get_exigence_nodes_from_texts(exigencies_texts, exact_match=exact_match)
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
        Takes an excel/dataframe with an 'Exigence' column, searches the graph, and appends
        'Phase projet', 'Métier', and 'Preuve de conformité' information connected to each exigence.

        Args:
            data_source (Union[str, pd.DataFrame]): Path to the data file or a pandas DataFrame.

        Returns:
            pd.DataFrame: A new DataFrame with the appended graph information.
        """
        df = load_and_clean_data(data_source)
        df_clean = df.copy()

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

        Args:
            spec_ids (List[str]): List of specification IDs.
            contract_ids (List[str]): List of contract IDs.

        Returns:
            List[Tuple[Node, bool]]: List of tuples containing the Exigence node and a boolean flag.
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
        """
        Returns Exigence descriptions connected to given specifications AND whose Preuves are linked to the given contracts.

        Args:
            spec_ids (List[str]): List of specification IDs.
            contract_ids (List[str]): List of contract IDs.

        Returns:
            List[str]: List of exigence descriptions.
        """
        data = self._get_spec_contract_exigences(spec_ids, contract_ids)
        return list({exg.metadata.get("description", "") for exg, is_linked in data if is_linked})

    def get_exigencies_by_specs_and_contracts_not_linked(self, spec_ids: List[str], contract_ids: List[str]) -> List[str]:
        """
        Returns Exigence descriptions connected to given specifications AND whose Preuves are NOT linked to the given contracts.

        Args:
            spec_ids (List[str]): List of specification IDs.
            contract_ids (List[str]): List of contract IDs.

        Returns:
            List[str]: List of exigence descriptions.
        """
        data = self._get_spec_contract_exigences(spec_ids, contract_ids)
        return list({exg.metadata.get("description", "") for exg, is_linked in data if not is_linked})

    def get_exigencies_linked_to_multiple_specs(self, spec_ids: List[str]) -> List[str]:
        """
        Returns exigencies that are connected to AT LEAST TWO different specifications from the provided list.

        Args:
            spec_ids (List[str]): List of specification IDs to check against.

        Returns:
            List[str]: List of exigence descriptions linked to multiple specs.
        """
        exigence_spec_count = {}
        for s_id in spec_ids:
            exigences = self.qry.get_neighbors(s_id, NodeType.EXIGENCE)
            for exg in exigences:
                exigence_spec_count[exg.id] = exigence_spec_count.get(exg.id, 0) + 1

        multi_spec_exgs = [exg_id for exg_id, count in exigence_spec_count.items() if count >= 2]
        return [self.qry.get_node(e_id).metadata.get("description", "") for e_id in multi_spec_exgs]

    def get_specifications_for_project(self, project_name: str) -> List[str]:
        """
        Given a project name, returns the list of specification names related to it.
        Relation: Project -> Exigence <- Specification

        Args:
            project_name (str): The name of the project.

        Returns:
            List[str]: List of specification names.
        """
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
        Strict traversal is used to avoid incorrectly merging paths via shared nodes (like Loi).

        Args:
            project_name (str): The name of the project.

        Returns:
            List[str]: List of linked contract names.
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
        From a list of Preuve texts, returns the list of Loi names related to them.
        Relation: Preuve -> Exigence -> Loi.

        Args:
            preuve_texts (List[str]): A list of Proof (Preuve) descriptions/texts.

        Returns:
            List[str]: A deduplicated list of related Law (Loi) names.
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

    def get_total_node_count(self) -> int:
        """
        Returns the total number of nodes in the graph.

        Returns:
            int: The total number of nodes.
        """
        return len(self.qry.get_all_nodes())

    def get_exigences_for_project(self, project_name: str) -> List[Node]:
        """
        Returns the list of Exigence nodes linked to a given project.

        Args:
            project_name (str): The name of the project.

        Returns:
            List[Node]: A list of Exigence nodes linked to the project.
        """
        proj_node = self.qry.find_node_by_exact_metadata("name", project_name, NodeType.PROJET)
        if not proj_node:
            return []
        return self.qry.get_neighbors(proj_node.id, NodeType.EXIGENCE)

    def get_exigences_count_for_project(self, project_name: str) -> int:
        """
        Returns the number of Exigence nodes linked to a given project.

        Args:
            project_name (str): The name of the project.

        Returns:
            int: The number of Exigence nodes.
        """
        return len(self.get_exigences_for_project(project_name))

    def get_exigences_with_rex_for_project(self, project_name: str) -> List[Node]:
        """
        Returns the list of Exigence nodes linked to a given project that also have at least one REX.

        Args:
            project_name (str): The name of the project.

        Returns:
            List[Node]: A list of Exigence nodes linked to the project and to a REX.
        """
        exigences = self.get_exigences_for_project(project_name)
        exigences_with_rex = []
        for exg in exigences:
            rex_nodes = self.qry.get_neighbors(exg.id, NodeType.REX)
            if rex_nodes:
                exigences_with_rex.append(exg)
        return exigences_with_rex

    def get_exigences_count_with_rex_for_project(self, project_name: str) -> int:
        """
        Returns the number of Exigence nodes linked to a given project that also have at least one REX.

        Args:
            project_name (str): The name of the project.

        Returns:
            int: The number of Exigence nodes.
        """
        return len(self.get_exigences_with_rex_for_project(project_name))

    def get_exigences_for_project_and_metier(self, project_name: str, metier_name: str) -> List[Node]:
        """
        Returns the list of Exigence nodes linked to a given project and a given Métier.

        Args:
            project_name (str): The name of the project.
            metier_name (str): The name of the métier.

        Returns:
            List[Node]: A list of Exigence nodes matching both project and métier.
        """
        exigences = self.get_exigences_for_project(project_name)
        matched_exigences = []
        for exg in exigences:
            metiers = self.qry.get_neighbors(exg.id, NodeType.METIER)
            if any(m.metadata.get("name") == metier_name for m in metiers):
                matched_exigences.append(exg)
        return matched_exigences

    def get_exigences_count_for_project_and_metier(self, project_name: str, metier_name: str) -> int:
        """
        Returns the number of Exigence nodes linked to a given project and a given Métier.

        Args:
            project_name (str): The name of the project.
            metier_name (str): The name of the métier.

        Returns:
            int: The number of Exigence nodes.
        """
        return len(self.get_exigences_for_project_and_metier(project_name, metier_name))

    def get_connected_nodes(
        self,
        source_node_ids: List[str],
        target_type: Optional[NodeType] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, List[Node]]:
        """
        Generically gets the number and list of unique nodes connected to the given source nodes.
        Optionally filters by the target node type and specific metadata criteria.

        Args:
            source_node_ids (List[str]): The IDs of the starting nodes.
            target_type (Optional[NodeType]): Only return connected nodes of this type.
            metadata_filters (Optional[Dict[str, Any]]): Only return nodes matching these metadata key-value pairs.

        Returns:
            Tuple[int, List[Node]]: The count and the list of unique matching connected nodes.
        """
        connected_nodes_set = set()

        for source_id in source_node_ids:
            neighbors = self.qry.get_neighbors(source_id, filter_type=target_type)
            for neighbor in neighbors:
                if metadata_filters:
                    match = True
                    for k, v in metadata_filters.items():
                        if neighbor.metadata.get(k) != v:
                            match = False
                            break
                    if not match:
                        continue
                connected_nodes_set.add(neighbor)

        connected_nodes_list = list(connected_nodes_set)
        return len(connected_nodes_list), connected_nodes_list
