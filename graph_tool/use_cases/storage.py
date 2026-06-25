from ..domain.ports import IGraphStorage

class StorageHandler:
    def __init__(self, storage_repo: IGraphStorage):
        self.storage = storage_repo

    def save_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Saves the current state of the graph to a file.
        Supported formats: graphml, json, pickle.
        """
        self.storage.save_graph(filepath, format)

    def load_graph(self, filepath: str, format: str = "graphml") -> None:
        """
        Loads a graph from a file, replacing the current state.
        Supported formats: graphml, json, pickle.
        """
        self.storage.load_graph(filepath, format)
