from abc import ABC, abstractmethod
from typing import Any
from ...domain.ports import IGraphQuery

class GraphRenderer(ABC):
    """
    Abstract base class for graph rendering engines.
    """

    @abstractmethod
    def render(self, query_repo: IGraphQuery, output_file: str, **kwargs) -> Any:
        """
        Renders the graph.

        Args:
            query_repo (IGraphQuery): The interface to read the graph data.
            output_file (str): The path/name to save or output the rendering.
            **kwargs: Additional engine-specific configuration options.

        Returns:
            Any: The result of the rendering (e.g., file path, URL, or image object).
        """
        pass
