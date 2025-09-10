from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from dotenv import load_dotenv
import sqlite3
import requests
import os
from langchain_groq import ChatGroq

load_dotenv()

# -------------------
# 1. LLM
# -------------------
# GROQ_MODEL = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant")

# -------------------
# 2. Tools
# -------------------
# Tools
search_tool = DuckDuckGoSearchRun(region="us-en") # type: ignore

# Store your RapidAPI key in .env for security
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "real-time-amazon-data.p.rapidapi.com"

@tool("amazon_product_search")
def amazon_product_search(
    query: str,
    page: str = "1",
    country: str = "US",
    sort_by: str = "RELEVANCE",
    product_condition: str = "ALL",
    is_prime: str = "false",
    deals_and_discounts: str = "NONE",
) -> dict:
    """
    Search Amazon for products by keyword and return structured details.
    """

    # --- Coerce types ---
    try:
        page = int(page) # type: ignore
    except ValueError:
        page = 1 # type: ignore

    is_prime = str(is_prime).lower() in ["true", "1", "yes"] # type: ignore

    url = f"https://{RAPIDAPI_HOST}/search"
    params = {
        "query": query,
        "page": str(page),
        "country": country,
        "sort_by": sort_by,
        "product_condition": product_condition,
        "is_prime": str(is_prime).lower(),
        "deals_and_discounts": deals_and_discounts,
    }
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        products = [
            {
                "title": item.get("product_title"),
                "price": item.get("product_price"),
                "currency": item.get("currency"),
                "rating": item.get("product_star_rating"),
                "reviews": item.get("product_num_ratings"),
                "image": item.get("product_photo"),
                "link": item.get("product_url"),
            }
            for item in data.get("data", {}).get("products", [])
        ]

        return {"results": products[:5]}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

tools = [search_tool,amazon_product_search]
llm_with_tools = llm.bind_tools(tools)

# -------------------
# 3. State
# -------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------------------
# 4. Nodes
# -------------------
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

# -------------------
# 5. Checkpointer
# -------------------
# checkpointer = InMemorySaver()
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# -------------------
# 6. Graph
# -------------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)

# -------------------
# 7. Helper
# -------------------
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"]) # type: ignore
    return list(all_threads)

