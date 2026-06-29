from ..domain.ports import IGraphStorage

class StorageHandler:
    """
    Handles graph persistence operations by wrapping the IGraphStorage port.
    """

    def __init__(self, storage_repo: IGraphStorage):
        """
        Initializes the StorageHandler.

        Args:
            storage_repo (IGraphStorage): The storage repository implementation to use.
        """
        self.storage = storage_repo

    def save_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Saves the current state of the graph to a file.

        Args:
            filepath (str): The destination path for the saved file.
            format (str): The format to save the graph in. Supported formats: graphml, json, pickle. Defaults to "graphml".
        """
        self.storage.save_graph(filepath, format)

    def load_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Loads a graph from a file, replacing the current state.

        Args:
            filepath (str): The path to the file to load.
            format (str): The format of the file. Supported formats: graphml, json, pickle. Defaults to "graphml".
        """
        self.storage.load_graph(filepath, format)
