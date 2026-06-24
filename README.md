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

## Requirements

Install the necessary dependencies:

```bash
pip install networkx pandas thefuzz pyvis openpyxl
```

## Usage

### 1. Initializing the tool

```python
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.queries import QueryHandler
from graph_tool.use_cases.enhancements import GraphEnhancements

repo = NetworkXGraphRepository()
commands = CommandHandler(repo, repo)
queries = QueryHandler(repo)
enhancements = GraphEnhancements(repo)
```

### 2. Adding Data (Commands)

The tool accepts Pandas DataFrames or paths to Excel (`.xlsx`) / `.csv` files.

- `commands.add_project_exigences(project_name, df_or_filepath)`
- `commands.add_rex(project_name, df_or_filepath)`
- `commands.add_specification(spec_id, spec_name, df_or_filepath)`
- `commands.add_contract(contract_id, contract_name, df_or_filepath)`

### 3. Querying Data

You can extract insights from the graph using the `QueryHandler`:
- `queries.find_most_similar_projects(...)`: Finds projects sharing the most exigencies.
- `queries.get_useful_rex(...)`: Gets Return on Experience (REX) from similar projects.
- `queries.complete_excel_with_graph_info(...)`: Takes an Excel of exigencies and appends connected Phase, Métier, and Preuve data.
- ...and many more complex transitive queries regarding Specifications and Contracts.

### 4. Enhancements

- **Graph Visualization:** Export your graph to an interactive HTML file.
  ```python
  enhancements.visualize_graph("output.html")
  ```
- **Integrity Checker:** Find dangling nodes (e.g., Exigences without a Preuve).
  ```python
  issues = enhancements.check_graph_integrity()
  ```

## Testing

Run the test suite via standard unittest:
```bash
python3 -m unittest discover tests
```