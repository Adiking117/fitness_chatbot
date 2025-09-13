from db.checkpoint import get_checkpointer
from graph.build_graph import build_graph
from utils.threads import retrieve_all_threads

checkpointer = get_checkpointer()
chatbot = build_graph(checkpointer)

# Example usage
# result = chatbot.invoke({"messages": [...]})
# threads = retrieve_all_threads(checkpointer)
