import os
import pandas as pd
from datetime import datetime
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.queries import QueryHandler
from graph_tool.use_cases.enhancements import GraphEnhancements
from graph_tool.use_cases.renderers import PyVisRenderer #, DatashaderRenderer

from graph_tool.use_cases.storage import StorageHandler
from graph_tool.use_cases.extractors import CreateExigenceAndArticlesStep, LinkMetierStep, LinkPhaseProjetStep
from graph_tool.domain.entities import NodeType

def main():
    print("Initializing the Graph Tool...")
    # 1. Initialize the graph components
    repo = NetworkXGraphRepository()
    # Provide the repository as both command and query interface
    commands = CommandHandler(repo, repo)
    queries = QueryHandler(repo)
    enhancements = GraphEnhancements(repo)
    storage = StorageHandler(repo)

    # 2. File paths for the generated dummy data
    file_project_A = "project_A.xlsx"
    file_project_B = "project_B.xlsx"
    file_project_C = "project_C.xlsx"
    file_rex_A = "rex_project_A.xlsx"

    # Optional: Set a file to load an existing graph from (e.g. "my_graph.graphml")
    # Comment out or set to None to start from an empty graph
    graph_file_to_load = None

    if graph_file_to_load and os.path.exists(graph_file_to_load):
        print(f"\n--- Loading Existing Graph from {graph_file_to_load} ---")
        storage.load_graph(graph_file_to_load)
    else:
        print("\n--- Starting with an empty graph ---")

    print("\n--- Loading Data ---")

    # Load exigencies for 3 different projects
    print("Loading Project A...")
    commands.add_project_exigences("Project A", file_project_A,steps=[CreateExigenceAndArticlesStep(), LinkMetierStep(), LinkPhaseProjetStep()])

    print("Loading Project B...")
    commands.add_project_exigences("Project B", file_project_B,steps=[CreateExigenceAndArticlesStep(), LinkMetierStep(), LinkPhaseProjetStep()])

    print("Loading Project C...")
    commands.add_project_exigences("Project C", file_project_C)

    # Load REX for Project A
    print("Loading REX for Project A...")
    commands.add_rex("Project A", file_rex_A,exact_match_only=True)

    print("\nData loaded successfully!")

    print("\n--- Running Queries ---")

    # Newly Added Questions

    print("\nQuestion: How many nodes the graph has?")
    total_nodes = queries.get_total_node_count()
    print(f"Answer: The graph has {total_nodes} nodes.")

    print("\nQuestion: What are the exigences linked to REX of Project A, that are in Project B but not Project A?")
    exgs_from_rex_b_not_a = queries.get_exigences_from_rex_for_target_not_source("Project A", "Project B")
    print(f"Answer: Found {len(exgs_from_rex_b_not_a)} exigences.")
    for exg in exgs_from_rex_b_not_a:
        print(f"  - Exigence ID: {exg.id}, Text: {exg.metadata.get('description', '')}")

    print("\nQuestion: How many exigences has the project A?")
    project_a_exg_count = queries.get_exigences_count_for_project("Project A")
    print(f"Answer: Project A has {project_a_exg_count} exigences.")

    print("\nQuestion: How many exigences with REX has the project A?")
    project_a_exg_rex_count = queries.get_exigences_count_with_rex_for_project("Project A")
    print(f"Answer: Project A has {project_a_exg_rex_count} exigences with REX.")

    test_metier = "Mécanique"
    print(f"\nQuestion: How many exigences are linked to Project A and the Métier '{test_metier}'?")
    count_proj_metier = queries.get_exigences_count_for_project_and_metier("Project A", test_metier)
    print(f"Answer: Project A has {count_proj_metier} exigences linked to {test_metier}.")

    print("\nQuestion: Generic search - How many REX nodes are connected to Project A's exigences?")
    proj_a_node = repo.find_node_by_exact_metadata("name", "Project A", NodeType.PROJET)
    if proj_a_node:
        proj_a_exg_nodes = queries.get_exigences_for_project("Project A")
        exg_ids = [n.id for n in proj_a_exg_nodes]
        rex_count, rex_nodes = queries.get_connected_nodes(source_node_ids=exg_ids, target_type=NodeType.REX)
        print(f"Answer: There are {rex_count} REX nodes connected to Project A's exigences.")
        for r in rex_nodes[:2]:
            print(f"  - REX snippet: {r.metadata.get('description', '')[:50]}...")
        if rex_count > 2:
            print(f"  - ... and {rex_count - 2} more.")

    # Question 1: Find similar projects to Project A based on its exigencies
    # Let's extract the exigencies text from Project A's dataframe for the query
    df_a = pd.read_excel(file_project_A)
    exigencies_a = df_a["Exigence"].dropna().tolist() if "Exigence" in df_a.columns else df_a.get("Exigences", pd.Series()).dropna().tolist()

    print(f"Question: What are the most similar projects to Project A?")
    similar_projects = queries.find_most_similar_projects("Project A", exigencies_a, top_k=2,exact_match=True)
    print(f"Answer: {similar_projects}")

    # Question 2: Get useful REX for Project B based on its exigencies
    df_b = pd.read_excel(file_project_B)
    exigencies_b = df_b["Exigence"].dropna().tolist() if "Exigence" in df_b.columns else df_b.get("Exigences", pd.Series()).dropna().tolist()

    print(f"\nQuestion: Are there any useful REX for Project B from similar projects?")
    # This function uses the find_most_similar_projects internally to find REX
    useful_rex_ids = queries.get_useful_rex("Project B", exigencies_b,exact_match=True)
    print(f"Answer: Found {len(useful_rex_ids)} relevant REX.")
    for rex_id in useful_rex_ids[:3]:
        # Retrieve the node to display its details
        node = repo.get_node(rex_id)
        if node:
             print(f"  - REX ID: {rex_id}, Source Exigence: {node.metadata.get('source_text')}")


    # Question 3: Complete an Excel with graph info (Testing with Project C's list)
    print(f"\nQuestion: Can we enrich Project C's data with details from the graph?")
    enriched_df = queries.complete_excel_with_graph_info(file_project_C)
    print(f"Answer: Yes. First requirement enriched data:")
    # Print out the first row's enriched data for demonstration
    if not enriched_df.empty:
        first_row = enriched_df.iloc[0]
        print(f"  Exigence: {first_row.get('Exigence', '')}")
        print(f"  Phase: {first_row.get('Phase projet (Graph)', '')}")
        print(f"  Métier: {first_row.get('Métier (Graph)', '')}")
        print(f"  Preuve: {first_row.get('Preuve de conformité (Graph)', '')}")

    # Question 4: Find similar exigencies for Project C
    df_c = pd.read_excel(file_project_B)
    exigencies_c = df_c["Exigence"].dropna().tolist() if "Exigence" in df_c.columns else df_c.get("Exigences", pd.Series()).dropna().tolist()
    print(f"\nQuestion: What are the most similar exigencies in the graph to those in Project C?")
    similar_exigencies_df = queries.find_most_similar_exigencies(exigencies_c)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    similar_exigencies_filename = f"similar_exigencies_{timestamp}.xlsx"
    similar_exigencies_df.to_excel(similar_exigencies_filename, index=False)
    print(f"Answer: Found similar exigencies. Results saved to {similar_exigencies_filename}")

    # NEW QUESTION
    print(f"\nQuestion: Can we get the list of Preuves and Phases for a specific list of Exigences?")
    input_file_path = "input_file.xlsx"
    if os.path.exists(input_file_path):
        preuves_df = queries.get_preuves_and_phases_for_exigences(input_file_path)
        output_file_path = "export_list_preuves_attendues.xlsx"
        preuves_df.to_excel(output_file_path, index=False)
        print(f"Answer: Yes. Results saved to {output_file_path}")
    else:
        print(f"Answer: Could not find {input_file_path}.")

    print("\n--- Enhancements ---")

    # Run Graph Integrity Check
    print("Checking graph integrity...")
    integrity_issues = enhancements.check_graph_integrity()
    if integrity_issues:
        print(f"Found {len(integrity_issues)} potential integrity issues. (These are expected depending on incomplete data links)")
    else:
        print("Graph integrity looks perfect.")

    # Visualize the Graph
    print(f"\nGenerating visualizations of the graph...")

    output_html_pyvis = "graph_visualization_pyvis.html"
    print(f"  -> Rendering with PyVis...")
    enhancements.visualize_graph(output_html_pyvis, renderer=PyVisRenderer())
    print(f"     PyVis visualization saved to {output_html_pyvis}")

    """
    output_html_ds = "graph_visualization_datashader.html"
    print(f"  -> Rendering with Datashader (force-directed layout)...")
    enhancements.visualize_graph(output_html_ds, renderer=DatashaderRenderer(), layout='spring')
    print(f"     Datashader visualization saved to {output_html_ds}")
    """

    print(f"  -> Generating Venn Diagram of Shared Exigences...")
    venn_filename = f"venn_diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    res_venn = enhancements.generate_venn_diagram_html(
        ensemble_type=NodeType.PROJET,
        element_type=NodeType.EXIGENCE,
        target_ensembles=["Project A", "Project B", "Project C"],
        output_file=venn_filename
    )
    if res_venn:
        print(f"     Venn diagram saved to {res_venn}")

    print("\n--- Saving the Graph ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_filename = f"graph_{timestamp}.graphml"
    storage.save_graph(save_filename)
    print(f"Graph saved successfully to {save_filename} with horodate.")

if __name__ == "__main__":
    main()
