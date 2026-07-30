import pandas as pd
from typing import List, Dict, Any, Union, Set, Tuple, Optional
from ..domain.entities import Node, NodeType
from ..domain.ports import IGraphQuery
from ..utils.text_utils import generate_short_id, find_best_match, find_best_match_with_score
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

    def get_exigences_from_rex_for_target_not_source(self, source_project_name: str, target_project_name: str) -> List[Node]:
        """
        Find REX for the source project.
        Find exigencies for these REX.
        Out of these exigencies, find those that are linked to the target project but not connected to the source project.

        Args:
            source_project_name (str): The name of the source project (e.g., "Project A").
            target_project_name (str): The name of the target project (e.g., "Project B").

        Returns:
            List[Node]: A list of Exigence nodes.
        """
        source_proj_node = self.qry.find_node_by_exact_metadata("name", source_project_name, NodeType.PROJET)
        target_proj_node = self.qry.find_node_by_exact_metadata("name", target_project_name, NodeType.PROJET)

        if not source_proj_node or not target_proj_node:
            return []

        # Find REX nodes connected to the source project
        source_rex_nodes = self.qry.get_neighbors(source_proj_node.id, NodeType.REX)

        # Collect all unique exigencies connected to these REX nodes
        exigences = set()
        for rex in source_rex_nodes:
            rex_exg_nodes = self.qry.get_neighbors(rex.id, NodeType.EXIGENCE)
            for exg in rex_exg_nodes:
                exigences.add(exg)

        # Filter the exigencies
        result = []
        for exg in exigences:
            exg_projects = self.qry.get_neighbors(exg.id, NodeType.PROJET)
            project_ids = {p.id for p in exg_projects}

            if target_proj_node.id in project_ids and source_proj_node.id not in project_ids:
                result.append(exg)

        return result

    def export_dict_to_excel(self, data: Dict[str, List[str]], filepath: str, key_col_name: str = "Key", val_col_name: str = "Values") -> None:
        """
        Exports a dictionary mapping strings to lists of strings into a 2-column Excel file.

        Args:
            data (Dict[str, List[str]]): The dictionary to export.
            filepath (str): The path where the Excel file should be saved.
            key_col_name (str, optional): The header for the first column. Defaults to "Key".
            val_col_name (str, optional): The header for the second column. Defaults to "Values".
        """
        rows = []
        for key, values in data.items():
            rows.append({
                key_col_name: key,
                val_col_name: ", ".join(values)
            })

        df = pd.DataFrame(rows)
        df.to_excel(filepath, index=False)

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


    def get_preuves_and_phases_for_exigences(self, data_source: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Reads a list of Exigences from the data source, looks for them in the graph,
        and retrieves their connected 'Preuve' and 'Phase projet' nodes.
        Returns a DataFrame with columns 'Exigences', 'Phase', 'Preuve'.
        Duplicates the row if there are multiple phases or preuves.
        If an Exigence is not found, its 'Phase' and 'Preuve' will be empty.

        Args:
            data_source (Union[str, pd.DataFrame]): Path to the excel file or DataFrame.

        Returns:
            pd.DataFrame: A new DataFrame with the requested format.
        """
        df = load_and_clean_data(data_source)

        results = []
        for _, row in df.iterrows():
            exigence_text = str(row.get("Exigences", "")).strip()
            if not exigence_text:
                continue

            nodes = self._get_exigence_nodes_from_texts([exigence_text], exact_match=True)
            if not nodes:
                results.append({"Exigences": exigence_text, "Phase": "", "Preuve": ""})
                continue

            exg_node = nodes[0]
            neighbors = self.qry.get_neighbors(exg_node.id)

            phases = [n.metadata.get("name", "") for n in neighbors if n.type == NodeType.PHASE_PROJET]
            preuves = [n.metadata.get("description", "") for n in neighbors if n.type == NodeType.PREUVE]

            if not phases and not preuves:
                results.append({"Exigences": exigence_text, "Phase": "", "Preuve": ""})
            else:
                if not phases:
                    phases = [""]
                if not preuves:
                    preuves = [""]

                # The prompt asks for: "Get also the «Phase» type node connected to each «preuve»."
                # However, in our schema, 'Phase' and 'Preuve' are both connected to 'Exigence', not directly to each other.
                # So we cross join phases and preuves for the current exigence.
                for phase in phases:
                    for preuve in preuves:
                        results.append({"Exigences": exigence_text, "Phase": phase, "Preuve": preuve})

        return pd.DataFrame(results)

    def complete_pivot_excel_with_graph_info(self, data_source: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Takes a flattened (1-row header) pivot DataFrame or Excel file, searches the graph,
        and completes the "Phase" and "Métier" columns for each requirement (Exigence).

        Args:
            data_source (Union[str, pd.DataFrame]): Path to the data file or a pandas DataFrame.

        Returns:
            pd.DataFrame: A new DataFrame with the graph information filled in.
        """
        df = load_and_clean_data(data_source)
        df_clean = df.copy()

        for idx, row in df_clean.iterrows():
            exigence_text = str(row.get("Exigences", "")).strip()
            if not exigence_text:
                continue

            nodes = self._get_exigence_nodes_from_texts([exigence_text], exact_match=True)
            if not nodes:
                continue

            exg_node = nodes[0]
            neighbors = self.qry.get_neighbors(exg_node.id)

            phases = [n for n in neighbors if n.type == NodeType.PHASE_PROJET]
            preuves = [n for n in neighbors if n.type == NodeType.PREUVE]

            # Complete Phase columns
            for p in phases:
                p_name = p.metadata.get("name")
                col_name = p_name if p_name in ["Conception", "Exploitation", "Commun"] else f"Phase {p_name}"
                if col_name in df_clean.columns:
                    df_clean.at[idx, col_name] = "X"

            # Complete Preuves, Métiers, and Documents
            for prv in preuves:
                prv_neighbors = self.qry.get_neighbors(prv.id)
                metiers = [n for n in prv_neighbors if n.type == NodeType.METIER]
                docs = [n for n in prv_neighbors if n.type == NodeType.DOCUMENT]

                for m in metiers:
                    m_name = m.metadata.get("name")
                    m_concerne = f"{m_name}_Concerné"
                    m_prv = f"{m_name}_Preuve de conformité"
                    m_ged = f"{m_name}_Reference GED PC"

                    if m_concerne in df_clean.columns:
                        df_clean.at[idx, m_concerne] = "X"

                    if m_prv in df_clean.columns:
                        # Append if already exists, or just set it
                        current_prv = str(df_clean.at[idx, m_prv]).strip()
                        new_prv = prv.metadata.get("description", "")
                        if new_prv:
                            if current_prv and current_prv != "nan" and current_prv != new_prv:
                                df_clean.at[idx, m_prv] = f"{current_prv} ; {new_prv}"
                            elif not current_prv or current_prv == "nan":
                                df_clean.at[idx, m_prv] = new_prv

                    if m_ged in df_clean.columns:
                        doc_names = [d.metadata.get("name", "") for d in docs]
                        new_ged = " ; ".join(doc_names)
                        if new_ged:
                            current_ged = str(df_clean.at[idx, m_ged]).strip()
                            if current_ged and current_ged != "nan" and current_ged != new_ged:
                                df_clean.at[idx, m_ged] = f"{current_ged} ; {new_ged}"
                            elif not current_ged or current_ged == "nan":
                                df_clean.at[idx, m_ged] = new_ged

        return df_clean


    def transform_to_2row_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms a flattened 1-row header pivot DataFrame back into its original
        2-row header MultiIndex structure.

        Args:
            df (pd.DataFrame): The flattened DataFrame.

        Returns:
            pd.DataFrame: A new DataFrame with a MultiIndex columns structure.
        """
        multi_cols = []
        for col in df.columns:
            # Check for known prefixes based on the pivot format
            if col.startswith("Data_"):
                multi_cols.append(("Data", col.replace("Data_", "")))
            elif col == "Data":
                multi_cols.append(("Data", "Line"))
            elif col in ["Article", "Article_texte", "Sous_Article", "Exigences", "Etat de Conformité", "Commentaire lié à la conformité", "textes à enjeux", "Commentaire général", "À Enjeux", "Conception", "Exploitation", "Commun", "Phase Etude", "Phase Contrat", "Phase Réalisation"]:
                # To match exact output, some originally un-named levels become part of the tuple, but usually they are flat headers
                multi_cols.append((col, "Unnamed"))
            elif "_" in col and (col.endswith("_Concerné") or col.endswith("_Preuve de conformité") or col.endswith("_Reference GED PC") or col.endswith("_Numéro de la preuve de conformité") or col.endswith("_Suivi de la preuve de conformité")):
                parts = col.rsplit("_", 1)
                multi_cols.append((parts[0], parts[1]))
            else:
                multi_cols.append((col, "Unnamed"))

        df_multi = df.copy()
        df_multi.columns = pd.MultiIndex.from_tuples(multi_cols)
        return df_multi

    def complete_excel_with_graph_info(self, data_source: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Takes an excel/dataframe with an 'Exigence' column, searches the graph, and appends
        'Phase projet', 'Métier', and 'Preuve de conformité' information connected to each exigence.

        Args:
            data_source (Union[str, pd.DataFrame]): Path to the data file or a pandas DataFrame.

        Returns:
            pd.DataFrame: A new DataFrame with the appended graph information.
        """
        from collections import defaultdict

        df = load_and_clean_data(data_source)
        df_clean = df.copy()

        phases_list = []
        metiers_list = []
        preuves_list = []

        # We will accumulate updates to apply to the dataframe later
        # However, to avoid overwriting existing columns, we initialize updates using existing columns if they exist.
        updates = defaultdict(lambda: [""] * len(df_clean))
        for col in df_clean.columns:
            updates[col] = df_clean[col].astype(str).tolist()

        for i, (idx, row) in enumerate(df_clean.iterrows()):

            article_name = str(row.get("Article", "")).strip()
            sous_article_name = str(row.get("Sous_Article", "")).strip()
            exigence_text = str(row.get("Exigences", "")).strip()
            if not exigence_text:
                phases_list.append("")
                metiers_list.append("")
                preuves_list.append("")
                continue

            exg_id = generate_short_id("EXG", article_name + sous_article_name + exigence_text)
            exg_node = self.qry.get_node(exg_id)
            if not exg_node:
                phases_list.append("")
                metiers_list.append("")
                preuves_list.append("")
                continue
            neighbors = self.qry.get_neighbors(exg_node.id)

            phases = [n.metadata.get("name", "") for n in neighbors if n.type == NodeType.PHASE_PROJET]
            metiers = [n.metadata.get("name", "") for n in neighbors if n.type == NodeType.METIER]
            preuves = [n.metadata.get("description", "") for n in neighbors if n.type == NodeType.PREUVE]

            phases_list.append(", ".join(phases))
            metiers_list.append(", ".join(metiers))
            preuves_list.append(", ".join(preuves))

            # --- New Logic ---
            # 1. Add "X" to phase column
            for phase in phases:
                if phase:
                    updates[phase][i] = "X"

            # 2. Add "X" to métier concerne column
            for metier in metiers:
                if metier:
                    updates[f"{metier}_Concerné"][i] = "X"

            # 3. Add Preuve to métier preuve column
            # We get preuves, then metier and phase related to each preuve.
            # But the requirement specified: "get the «Preuve» type nodes related. Then get the «métier» type and the Phase_projet type nodes related to the preuve."
            # Note: based on the user's answer, there should be a link between PREUVE and METIER / PHASE_PROJET
            preuve_nodes = [n for n in neighbors if n.type == NodeType.PREUVE]

            for p_node in preuve_nodes:
                p_text = p_node.metadata.get("description", "")
                if not p_text:
                    continue

                # Fetch related metier and phase for THIS preuve
                p_neighbors = self.qry.get_neighbors(p_node.id)
                p_metiers = [n.metadata.get("name", "") for n in p_neighbors if n.type == NodeType.METIER]
                p_phases = [n.metadata.get("name", "") for n in p_neighbors if n.type == NodeType.PHASE_PROJET]

                for metier in p_metiers:
                    # Ajouter la preuve uniquement si le métier est concerné
                    col_concerne = f"{metier}_Concerné"
                    if str(updates[col_concerne][i]).strip().upper() != "X":
                        continue

                    col_name = f"{metier}_Preuve de conformité"

                    if p_phases:
                        strings_to_add = [
                            f"Phase {phase} : {p_text}"
                            for phase in p_phases
                        ]
                    else:
                        strings_to_add = [p_text]

                    for string_to_add in strings_to_add:
                        existing = updates[col_name][i]
                        if existing:
                            updates[col_name][i] = existing + "\n" + string_to_add
                        else:
                            updates[col_name][i] = string_to_add

        df["Phase projet (Graph)"] = phases_list
        df["Métier (Graph)"] = metiers_list
        df["Preuve de conformité (Graph)"] = preuves_list

        for col_name, col_data in updates.items():
            df[col_name] = col_data

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

    def get_preuves_connection_status_for_project(self, project_name: str) -> Tuple[List[Node], List[Node]]:
        """
        Retrieves two lists of Preuve nodes for a specific project:
        1. Preuve nodes that are NOT connected to a Document node.
        2. Preuve nodes that ARE connected to a Document node.

        Args:
            project_name (str): The name of the project to analyze.

        Returns:
            Tuple[List[Node], List[Node]]: A tuple containing two lists:
                - List of Preuve nodes without a connected Document.
                - List of Preuve nodes with a connected Document.
        """
        proj_node = self.qry.find_node_by_exact_metadata("name", project_name, NodeType.PROJET)
        if not proj_node:
            return [], []

        preuves_without_document = set()
        preuves_with_document = set()

        exigences = self.qry.get_neighbors(proj_node.id, NodeType.EXIGENCE)
        for exg in exigences:
            preuves = self.qry.get_neighbors(exg.id, NodeType.PREUVE)
            for p in preuves:
                documents = self.qry.get_neighbors(p.id, NodeType.DOCUMENT)
                if documents:
                    preuves_with_document.add(p)
                else:
                    preuves_without_document.add(p)

        return list(preuves_without_document), list(preuves_with_document)

    def find_most_similar_exigencies(self, input_exigencies: List[str], threshold: int = 70) -> pd.DataFrame:
        """
        Takes a list of exigencies and looks into the graph for the most similar exigencies.

        Args:
            input_exigencies (List[str]): The list of input exigence descriptions.
            threshold (int): The minimum fuzzy match score (0-100) to accept a match. Defaults to 70.

        Returns:
            pd.DataFrame: A DataFrame with the input exigencies, the best matching exigencies from the graph, and the similarity scores.
        """
        all_exigence_nodes = self.qry.get_nodes_by_type(NodeType.EXIGENCE)
        graph_exigence_descriptions = [node.metadata.get("description", "") for node in all_exigence_nodes if node.metadata.get("description")]

        results = []
        for input_text in input_exigencies:
            if not input_text:
                results.append({"Input Exigence": input_text, "Best Match Exigence": None, "Similarity Score": None})
                continue

            best_match, score = find_best_match_with_score(input_text, graph_exigence_descriptions, threshold)
            results.append({
                "Input Exigence": input_text,
                "Best Match Exigence": best_match,
                "Similarity Score": score
            })

        return pd.DataFrame(results)

    def get_exigencies_with_multiple_sous_articles(self) -> Dict[str, List[str]]:
        """
        Gets the list of exigencies that are connected to several "Sous article" nodes.
        The result gives for each such exigence the list of "Sous-article" concerned.

        Returns:
            Dict[str, List[str]]: A dictionary mapping Exigence descriptions to lists of "Sous Article" names.
        """
        result = {}
        all_exigences = self.qry.get_nodes_by_type(NodeType.EXIGENCE)

        for exg in all_exigences:
            neighbors = self.qry.get_neighbors(exg.id, filter_type=NodeType.SOUS_ARTICLE)
            if len(neighbors) > 1:
                desc = exg.metadata.get("description", "")
                if desc:
                    result[desc] = [n.metadata.get("name", "") for n in neighbors]

        return result

    def get_sous_articles_with_multiple_articles(self) -> Dict[str, List[str]]:
        """
        Gets the list of "Sous-article" nodes connected to several "Article" nodes.
        Provides for each such "Sous-article" the list of Articles connected.

        Returns:
            Dict[str, List[str]]: A dictionary mapping "Sous Article" names to lists of "Article" names.
        """
        result = {}
        all_sous_articles = self.qry.get_nodes_by_type(NodeType.SOUS_ARTICLE)

        for sart in all_sous_articles:
            neighbors = self.qry.get_neighbors(sart.id, filter_type=NodeType.ARTICLE)
            if len(neighbors) > 1:
                name = sart.metadata.get("name", "")
                if name:
                    result[name] = [n.metadata.get("name", "") for n in neighbors]

        return result

    def get_preuves_phases_metiers_articles_for_exigences(
        self,
        project_name: str
    ) -> pd.DataFrame:
        """
        Récupère pour un projet l'ensemble des combinaisons :
        Preuve / Article / Domaine / Phase projet / Métier.

        Parcours :
        Projet -> Exigence
        Exigence -> Preuve
        Exigence -> Sous-Article -> Article -> Domaine
        Preuve -> Métier
        Preuve -> Phase Projet

        Returns:
            pd.DataFrame avec les colonnes :
            Preuves, Article, Domaine, Phase, Métier
        """
        columns = ["Preuves", "Article", "Domaine", "Phase", "Métier"]

        proj_node = self.qry.find_node_by_exact_metadata(
            "name",
            project_name,
            NodeType.PROJET
        )

        if not proj_node:
            return pd.DataFrame(columns=columns)

        results = []

        exigences = self.qry.get_neighbors(
            proj_node.id,
            NodeType.EXIGENCE
        )

        for exg in exigences:

            # ---------- Articles et domaines ----------
            articles_data = []

            sous_articles = self.qry.get_neighbors(
                exg.id,
                NodeType.SOUS_ARTICLE
            )

            for sous_article in sous_articles:
                articles = self.qry.get_neighbors(
                    sous_article.id,
                    NodeType.ARTICLE
                )

                for article in articles:
                    article_name = article.metadata.get("name", "")

                    domains = self.qry.get_neighbors(
                        article.id,
                        NodeType.DOMAIN
                    )

                    # Un article doit être lié à un seul domaine
                    domain_name = (
                        domains[0].metadata.get("name", "")
                        if domains
                        else ""
                    )

                    articles_data.append(
                        (article_name, domain_name)
                    )

            # Suppression des doublons Article / Domaine
            articles_data = list(set(articles_data))

            if not articles_data:
                articles_data = [("", "")]

            # ---------- Preuves ----------
            preuves = self.qry.get_neighbors(
                exg.id,
                NodeType.PREUVE
            )

            for preuve in preuves:
                preuve_text = (
                    preuve.metadata.get("description")
                    or preuve.metadata.get("name")
                    or ""
                )

                preuve_neighbors = self.qry.get_neighbors(preuve.id)

                metiers = list({
                    node.metadata.get("name", "")
                    for node in preuve_neighbors
                    if node.type == NodeType.METIER
                    and node.metadata.get("name")
                })

                phases = list({
                    node.metadata.get("name", "")
                    for node in preuve_neighbors
                    if node.type == NodeType.PHASE_PROJET
                    and node.metadata.get("name")
                })

                if not metiers:
                    metiers = [""]

                if not phases:
                    phases = [""]

                for article_name, domain_name in articles_data:
                    for phase in phases:
                        for metier in metiers:
                            results.append({
                                "Preuves": preuve_text,
                                "Article": article_name,
                                "Domaine": domain_name,
                                "Phase": phase,
                                "Métier": metier
                            })

        return pd.DataFrame(results, columns=columns).drop_duplicates()
