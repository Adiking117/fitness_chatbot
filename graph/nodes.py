from graph.state import ChatState
from langgraph.prebuilt import ToolNode
from llm.groq_llm import llm
from tools.search import search_tool
from tools.nutritionix import nutritionix_natural_nutrients, nutritionix_natural_exercise

tools = [search_tool, nutritionix_natural_nutrients, nutritionix_natural_exercise]
llm_with_tools = llm.bind_tools(tools)

def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)
