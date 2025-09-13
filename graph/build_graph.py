from langgraph.graph import StateGraph, START
from graph.state import ChatState
from graph.nodes import chat_node, tool_node
from langgraph.prebuilt import tools_condition

def build_graph(checkpointer):
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
    return graph.compile(checkpointer=checkpointer)
