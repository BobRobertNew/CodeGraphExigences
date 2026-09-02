# Python Graph Tool

A Python-based tool designed to manage an ontology of projects, requirements (exigences), laws (normes), proofs, specifications, and contracts. It utilizes a graph structure to connect these entities and allows for complex querying and visualization.

## Architecture & SOLID Principles

This tool strictly adheres to **SOLID** principles, specifically:
- **Dependency Inversion:** The core logic (Use Cases) interacts with abstract interfaces (`IGraphCommand`, `IGraphQuery`), meaning the graph database can be swapped (currently using `NetworkX`).
- **Single Responsibility Principle:** Code is cleanly separated into Domain (Entities), Infrastructure (Data Loading, NetworkX Repo), and Use Cases (Commands to modify data, Queries to read data).

### Project Structure
- `graph_tool/domain/`: Contains `Node`, `Edge`, `NodeType` enums, and Repository Interfaces.
- `graph_tool/infrastructure/`: Contains `NetworkXGraphRepository` (the concrete graph implementation) and `data_loader.py`.
- `graph_tool/use_cases/`: Contains `CommandHandler`, `QueryHandler`, and `GraphEnhancements`.
- `graph_tool/utils/`: Contains helpers for string hashing and fuzzy text matching.


## Architecture Philosophy

This tool uses a strict SOLID-compliant architecture designed around the principles of Dependency Inversion and CQRS (Command Query Responsibility Segregation).

*   **Domain**: At its core, the tool uses abstract `Node` and `Edge` definitions, completely agnostic of any specific database engine.
*   **Infrastructure**: Houses the actual persistence logic, currently implemented via `NetworkXGraphRepository`.
*   **Use Cases**: Divided cleanly into `commands` (actions that modify the graph, like loading Exigences or Contracts) and `queries` (actions that extract information, like finding similar projects).
*   **Decoupled Extraction**: Data ingestion is handled by an `IExtractionStep` interface. This allows developers to easily hot-swap parsing logic (e.g., `CreateExigenceAndArticlesStep`, `LinkMetierStep`) depending on the input data format, without touching the core command logic.
*   **Decoupled Rendering**: Graph visualizations are generated using a Strategy Pattern via the `GraphRenderer` interface. This means the core logic doesn't care if you are rendering with PyVis or Datashader, it just provides an `IGraphQuery` adapter to the renderer.

### Understanding `main.py`

The `main.py` file serves as the definitive, executable demonstration of the tool's capabilities. It acts as the composition root where all dependencies are wired together:

1.  **Initialization**: It spins up the `NetworkXGraphRepository` and injects it into the `CommandHandler`, `QueryHandler`, and `GraphEnhancements` services.
2.  **Data Loading**: It demonstrates how to seed the graph with data by processing multiple Excel files (`project_A.xlsx`, etc.) using specific extraction pipelines.
3.  **Queries in Action**: The script runs a suite of complex queries (e.g., finding identical exigences across different projects, filtering by specific Trades/Métiers, fetching linked REX notes) showcasing the power of the `QueryHandler`.
4.  **Enhancements & Visuals**: It executes integrity checks, computes Venn diagrams for overlapping requirements, UpSet plots, and exports a final navigable HTML graph.
5.  **Persistence**: Finally, it demonstrates how to save the graph state using `StorageHandler` for later use.

Reviewing `main.py` is the best starting point to understand how to interact with the API programmatically.

## Requirements

Install the necessary dependencies:

```bash
pip install networkx pandas rapidfuzz tqdm streamlit scipy datashader holoviews bokeh pytest pytest-cov matplotlib-venn sphinx sphinx-rtd-theme pyvis openpyxl upsetplot matplotlib
```

## Usage

### 1. Initializing the tool

```python
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.queries import QueryHandler
from graph_tool.use_cases.enhancements import GraphEnhancements
from graph_tool.use_cases.storage import StorageHandler
from graph_tool.use_cases.renderers import PyVisRenderer
from graph_tool.use_cases.extractors import CreateExigenceAndArticlesStep, LinkMetierStep, LinkPhaseProjetStep

repo = NetworkXGraphRepository()
commands = CommandHandler(repo, repo)
queries = QueryHandler(repo)
enhancements = GraphEnhancements(repo)
storage = StorageHandler(repo)
```

### 2. Adding Data (Commands)

The tool accepts Pandas DataFrames or paths to Excel (`.xlsx`) / `.csv` files.

- `commands.add_project_exigences(project_name, df_or_filepath, steps=[CreateExigenceAndArticlesStep(), LinkMetierStep(), LinkPhaseProjetStep()])`
- `commands.add_rex(project_name, df_or_filepath, exact_match_only=True)`
- `commands.add_specification(spec_id, spec_name, df_or_filepath)`
- `commands.add_contract(contract_id, contract_name, df_or_filepath)`

### 3. Querying Data

You can extract insights from the graph using the `QueryHandler`:
- `queries.find_most_similar_projects(...)`: Finds projects sharing the most exigencies.
- `queries.get_useful_rex(...)`: Gets Return on Experience (REX) from similar projects.
- `queries.complete_excel_with_graph_info(...)`: Takes an Excel of exigencies and appends connected Phase, Métier, and Preuve data.
- ...and many more complex transitive queries regarding Specifications and Contracts.

### 4. Saving and Loading the Graph

You can save and load the graph using `StorageHandler` to preserve its state without building it from scratch every time. Supported formats are `graphml` (default), `json`, and `pickle`.

```python
# Save the graph
storage.save_graph("my_graph.graphml", format="graphml")

# Load the graph
storage.load_graph("my_graph.graphml", format="graphml")
```

### 5. Enhancements

- **Graph Visualization:** Export your graph to an interactive HTML file using different renderers (e.g., PyVis, Datashader).
  ```python
  enhancements.visualize_graph("output.html", renderer=PyVisRenderer())
  ```
- **Venn Diagrams:** Generate HTML-based Venn diagrams for overlapping node sets.
  ```python
  enhancements.generate_venn_diagram_html(...)
  ```
- **UpSet Plots:** Generate UpSet plots for complex intersections.
  ```python
  enhancements.generate_upset_plot(...)
  ```

### 6. User Interface

You can launch the Streamlit-based web interface to interact with the graph visually:
```bash
streamlit run graph_tool/ui/app.py
```
- **Integrity Checker:** Find dangling nodes (e.g., Exigences without a Preuve).
  ```python
  issues = enhancements.check_graph_integrity()
  ```

## Testing

Run the test suite via standard unittest:
```bash
PYTHONPATH=. python3 -m pytest tests/
```