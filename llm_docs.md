# LLM Reference Documentation: Graph Tool Codebase

This document serves as a reference for a Large Language Model (LLM) or automated agent working with this Python-based graph management tool. The tool is designed to manage and query an ontology of project entities (e.g., Projet, Exigence, Loi, Phase projet, Métier, REX, Spécification, Contrat, Site, Document, Preuve, Article, Sous Article).

## Core Architecture and Principles

The system strictly adheres to **SOLID** principles, with a strong emphasis on **Dependency Inversion** and **CQRS (Command Query Responsibility Segregation)** patterns:
- **`IGraphQuery`**: Interface for reading/querying the graph (no mutations).
- **`IGraphCommand`**: Interface for writing/modifying the graph.
- **`IGraphStorage`**: Interface for saving/loading graph states (GraphML, GEXF, JSON, Pickle).

## Querying and Retrieving Data (Primary Focus)

Most questions require fetching and analyzing data from the graph. The `graph_tool.use_cases.queries.QueryHandler` provides the main business logic to fetch insights.

### Key Query Functions, Parameters, and Usage

*   **`find_most_similar_projects`**
    *   **Description**: Finds projects that share the most requirements (exigencies) with a given list.
    *   **Parameters**:
        *   `target_project_name` (`str`): The name of the baseline project to exclude from the results.
        *   `exigencies_texts` (`List[str]`): A list of requirement texts to compare against.
        *   `top_k` (`int`, optional, default=1): The maximum number of similar projects to return.
        *   `exact_match` (`bool`, optional, default=False): If True, skips fuzzy matching and looks for exact description matches.
    *   **Returns**: `List[str]` (List of similar project names).
    *   **Example**:
        ```python
        similar = query_handler.find_most_similar_projects("Project Alpha", ["Must be secure", "Fast response time"], top_k=2)
        ```

*   **`get_useful_rex`**
    *   **Description**: Extracts Return on Experience (REX) node IDs related to given requirements from up to 3 similar projects.
    *   **Parameters**:
        *   `project_name` (`str`): The name of the baseline project.
        *   `exigencies_texts` (`List[str]`): A list of requirement texts.
        *   `exact_match` (`bool`, optional, default=False): If True, skips fuzzy matching.
    *   **Returns**: `List[str]` (List of useful REX node IDs).
    *   **Example**:
        ```python
        rex_ids = query_handler.get_useful_rex("Project Alpha", ["Must be secure"])
        ```

*   **`complete_excel_with_graph_info`**
    *   **Description**: Takes a DataFrame or file with an 'Exigence' column and appends graph-derived information ('Phase projet', 'Métier', 'Preuve de conformité').
    *   **Parameters**:
        *   `data_source` (`Union[str, pd.DataFrame]`): Path to the Excel/CSV file or a pandas DataFrame.
    *   **Returns**: `pd.DataFrame` (A new DataFrame with appended columns).
    *   **Example**:
        ```python
        enriched_df = query_handler.complete_excel_with_graph_info("input_data.xlsx")
        ```

*   **`get_exigencies_by_specs_and_contracts_linked` / `_not_linked`**
    *   **Description**: Returns Exigence descriptions connected to given specifications AND whose Preuves are linked (or NOT linked) to the given contracts.
    *   **Parameters**:
        *   `spec_ids` (`List[str]`): List of specification IDs.
        *   `contract_ids` (`List[str]`): List of contract IDs.
    *   **Returns**: `List[str]` (List of exigence descriptions).
    *   **Example**:
        ```python
        linked_exgs = query_handler.get_exigencies_by_specs_and_contracts_linked(["SPEC-1"], ["CONT-A"])
        ```

*   **`get_specifications_for_project`** & **`get_contracts_for_project`**
    *   **Description**: Retrieves related specification names or contract names for a given project through graph traversal.
    *   **Parameters**:
        *   `project_name` (`str`): The name of the project.
    *   **Returns**: `List[str]` (List of specification or contract names).
    *   **Example**:
        ```python
        contracts = query_handler.get_contracts_for_project("Project Alpha")
        ```

*   **`get_connected_nodes`**
    *   **Description**: Generically gets the count and list of unique nodes connected to the given source nodes, optionally filtering by target type and metadata.
    *   **Parameters**:
        *   `source_node_ids` (`List[str]`): The IDs of the starting nodes.
        *   `target_type` (`Optional[NodeType]`, default=None): Only return connected nodes of this type.
        *   `metadata_filters` (`Optional[Dict[str, Any]]`, default=None): Only return nodes matching these metadata key-value pairs.
    *   **Returns**: `Tuple[int, List[Node]]` (The count and the list of unique matching connected nodes).
    *   **Example**:
        ```python
        from graph_tool.domain.entities import NodeType
        count, nodes = query_handler.get_connected_nodes(["EXG-123"], target_type=NodeType.METIER, metadata_filters={"name": "Software"})
        ```

*   **`find_most_similar_exigencies`**
    *   **Description**: Takes a list of exigencies and looks into the graph for the most similar exigencies using fuzzy matching.
    *   **Parameters**:
        *   `input_exigencies` (`List[str]`): The list of input exigence descriptions.
        *   `threshold` (`int`, optional, default=70): The minimum fuzzy match score (0-100) to accept a match.
    *   **Returns**: `pd.DataFrame` (DataFrame with 'Input Exigence', 'Best Match Exigence', and 'Similarity Score').
    *   **Example**:
        ```python
        df_matches = query_handler.find_most_similar_exigencies(["System must not crash"], threshold=80)
        ```

### Querying Initialization Boilerplate

```python
from graph_tool.infrastructure.networkx_adapter import NetworkXAdapter
from graph_tool.use_cases.queries import QueryHandler

# Initialize the query adapter and handler
query_adapter = NetworkXAdapter() # Typically, this adapter might already hold the loaded graph
query_handler = QueryHandler(query_adapter)
```

## Modifying Data (Commands)

To add data to the graph, use `graph_tool.use_cases.commands.CommandHandler`.

### Key Command Functions, Parameters, and Usage

*   **`add_project_exigences`**
    *   **Description**: Ingests project requirements from a data source. Supports custom extraction logic.
    *   **Parameters**:
        *   `project_name` (`str`): The name of the project.
        *   `data_source` (`Union[str, pd.DataFrame]`): Path to the Excel/CSV file or a pandas DataFrame.
        *   `loader` (`Callable`, optional): Function to load the data source (defaults to `load_and_clean_data`).
        *   `steps` (`List[IExtractionStep]`, optional): List of extraction steps to apply. If None, uses legacy logic.
    *   **Example**:
        ```python
        cmd_handler.add_project_exigences("Project Alpha", "project_reqs.xlsx")
        ```

*   **`add_rex`**
    *   **Description**: Adds Return on Experience notes linked to existing Exigences for a specific project.
    *   **Parameters**:
        *   `project_name` (`str`): The name of the project.
        *   `data_source` (`Union[str, pd.DataFrame]`): Path to the Excel/CSV file or a pandas DataFrame.
        *   `loader` (`Callable`, optional): Function to load the data source.
    *   **Example**:
        ```python
        cmd_handler.add_rex("Project Alpha", "rex_data.xlsx")
        ```

*   **`add_specification`**
    *   **Description**: Creates a Specification node and connects it to a list of Exigence nodes provided in the data source.
    *   **Parameters**:
        *   `spec_id` (`str`): The unique ID of the specification.
        *   `spec_name` (`str`): The name of the specification.
        *   `data_source` (`Union[str, pd.DataFrame]`): Path to the Excel/CSV file or a pandas DataFrame.
    *   **Example**:
        ```python
        cmd_handler.add_specification("SPEC-001", "Main Spec", "spec_data.xlsx")
        ```

*   **`add_contract`**
    *   **Description**: Creates a Contract node and connects it to Document nodes defined in the data source.
    *   **Parameters**:
        *   `contract_id` (`str`): The unique ID of the contract.
        *   `contract_name` (`str`): The name of the contract.
        *   `data_source` (`Union[str, pd.DataFrame]`): Path to the Excel/CSV file or a pandas DataFrame.
    *   **Example**:
        ```python
        cmd_handler.add_contract("CONT-99", "Vendor Contract", "contract_docs.xlsx")
        ```

### Command Initialization Boilerplate

```python
from graph_tool.infrastructure.networkx_adapter import NetworkXAdapter
from graph_tool.use_cases.commands import CommandHandler

command_adapter = NetworkXAdapter() # Typically shares the same underlying graph instance as query adapter
query_adapter = command_adapter
cmd_handler = CommandHandler(command_adapter, query_adapter)
```

## Data Loading Notes

The ingestion pipeline leverages `load_and_clean_data` from `graph_tool.infrastructure.data_loader`, which automatically detects multi-row headers across file formats by checking for 'Unnamed:' columns.

## Important Enums and Entities

The `graph_tool.domain.entities.NodeType` enum defines valid node types:
`PROJET`, `EXIGENCE`, `LOI`, `PHASE_PROJET`, `METIER`, `REX`, `SPECIFICATION`, `CONTRAT`, `SITE`, `DOCUMENT`, `PREUVE`, `ARTICLE`, `SOUS_ARTICLE`.
