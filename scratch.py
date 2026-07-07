from graph_tool.domain.entities import Node, NodeType
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.extractors import LinkPreuveStep
from graph_tool.utils.text_utils import generate_short_id
import pandas as pd

repo = NetworkXGraphRepository()
cmd_handler = CommandHandler(repo, repo)

exigence_text = "Test Exigence"
exg_id = generate_short_id("EXG", exigence_text)
exg_node = Node(id=exg_id, type=NodeType.EXIGENCE, metadata={"description": exigence_text})
cmd_handler.cmd.add_node(exg_node)

data = {
    "Exigences": [exigence_text],
    "MétierA_Concerné": ["X"],
    "MétierA_Preuve de conformité": ["Phase Etude: text 1. Phase Conception: text 2"]
}
df = pd.DataFrame(data)

step = LinkPreuveStep()
step.execute(df, None, cmd_handler.cmd, cmd_handler.qry)

preuves = repo.get_nodes_by_type(NodeType.PREUVE)
print(f"Preuves: {len(preuves)}")

edges = repo.get_all_edges()
prv_text1 = [p for p in preuves if p.metadata["description"] == "text 1."][0]
linked_to_prv = [e for e in edges if e.source_id == prv_text1.id or e.target_id == prv_text1.id]
print(f"Linked to Preuve: {len(linked_to_prv)}")
for e in linked_to_prv:
    print(f"Edge: {e.source_id} -> {e.target_id}")
