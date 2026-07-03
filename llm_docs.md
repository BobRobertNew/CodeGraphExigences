# LLM Reference Documentation: Graph Tool Codebase

This document serves as a reference for a Large Language Model (LLM) or automated agent working with this Python-based graph management tool. The tool is designed to manage and query an ontology of project entities (e.g., Projet, Exigence, Loi, Phase projet, Métier, REX, Spécification, Contrat, Site, Document, Preuve, Article, Sous Article).

## Core Architecture and Principles

The system strictly adheres to **SOLID** principles, with a strong emphasis on **Dependency Inversion** and **CQRS (Command Query Responsibility Segregation)** patterns:
- **`IGraphQuery`**: Interface for reading/querying the graph (no mutations).
- **`IGraphCommand`**: Interface for writing/modifying the graph.
- **`IGraphStorage`**: Interface for saving/loading graph states (GraphML, GEXF, JSON, Pickle).

## Querying and Retrieving Data (Primary Focus)

Most questions require fetching and analyzing data from the graph. The `graph_tool.use_cases.queries.QueryHandler` provides the main business logic to fetch insights.

### Key Query Capabilities

*   **Find Similar Projects (`find_most_similar_projects`)**: Given a project name and a list of exigence (requirement) texts, finds the `top_k` projects sharing the most requirements.
*   **Extract Useful REX (`get_useful_rex`)**: Gets Return on Experience (REX) notes related to given exigences from similar projects.
*   **Enrich Excel Data (`complete_excel_with_graph_info`)**: Takes a pandas DataFrame or file with an 'Exigence' column and appends graph-derived information ('Phase projet', 'Métier', 'Preuve de conformité').
*   **Specification & Contract Linkages**:
    *   `get_exigencies_by_specs_and_contracts_linked` / `not_linked`: Checks complex paths (Exigence -> Preuve -> Document -> Contrat).
    *   `get_specifications_for_project`: Gets specifications related to a project.
    *   `get_contracts_for_project`: Gets contracts related to a project.
    *   `get_exigencies_linked_to_multiple_specs`: Finds exigences shared by at least two specifications.
*   **Law (Loi) Extraction (`get_lois_from_preuves`)**: Finds related laws based on proof texts.
*   **Project-Specific Queries**:
    *   `get_exigences_for_project` (and `_count`)
    *   `get_exigences_with_rex_for_project` (and `_count`)
    *   `get_exigences_for_project_and_metier` (and `_count`)
*   **Generic Graph Traversal (`get_connected_nodes`)**: Explores neighbors of given nodes, optionally filtering by target type and metadata.
*   **Fuzzy Matching (`find_most_similar_exigencies`)**: Matches input texts against existing exigences in the graph.

### Querying Boilerplate

```python
from graph_tool.infrastructure.networkx_adapter import NetworkXAdapter
from graph_tool.use_cases.queries import QueryHandler
from graph_tool.domain.entities import NodeType

# Initialize the query adapter and handler
query_adapter = NetworkXAdapter() # Typically, this adapter might already hold the loaded graph
query_handler = QueryHandler(query_adapter)

# Example 1: Finding connected nodes directly
exigence_nodes = query_adapter.get_nodes_by_type(NodeType.EXIGENCE)

# Example 2: Using the QueryHandler for business logic
project_name = "Project Alpha"
requirements = ["The system must be secure", "Must be fast"]
similar_projects = query_handler.find_most_similar_projects(project_name, requirements, top_k=2)

# Example 3: Filtering neighbors
proj_node = query_adapter.find_node_by_exact_metadata("name", project_name, NodeType.PROJET)
if proj_node:
    neighbors = query_adapter.get_neighbors(proj_node.id, filter_type=NodeType.EXIGENCE)
```

## Modifying Data (Commands)

To add data to the graph, use `graph_tool.use_cases.commands.CommandHandler`.

### Key Command Capabilities
*   **`add_project_exigences`**: Ingests project requirements from a pandas DataFrame or Excel/CSV file. Supports plugging in custom extraction logic (`IExtractionStep`).
*   **`add_rex`**: Adds Return on Experience notes linked to existing Exigences.
*   **`add_specification`**: Adds specification nodes linked to exigences.
*   **`add_contract`**: Adds contract nodes linked to documents.

### Command Boilerplate

```python
from graph_tool.infrastructure.networkx_adapter import NetworkXAdapter
from graph_tool.use_cases.commands import CommandHandler

command_adapter = NetworkXAdapter() # Typically shares the same underlying graph instance as query adapter
query_adapter = command_adapter
cmd_handler = CommandHandler(command_adapter, query_adapter)

# Adding REX data from an Excel file
cmd_handler.add_rex(project_name="Project Alpha", data_source="rex_data.xlsx")
```

## Data Loading Notes

The ingestion pipeline leverages `load_and_clean_data` from `graph_tool.infrastructure.data_loader`, which automatically detects multi-row headers across file formats by checking for 'Unnamed:' columns.

## Important Enums and Entities

The `graph_tool.domain.entities.NodeType` enum defines valid node types:
`PROJET`, `EXIGENCE`, `LOI`, `PHASE_PROJET`, `METIER`, `REX`, `SPECIFICATION`, `CONTRAT`, `SITE`, `DOCUMENT`, `PREUVE`, `ARTICLE`, `SOUS_ARTICLE`.
