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

# Store your credentials in .env
NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_APP_KEY = os.getenv("NUTRITIONIX_APP_KEY")

from langchain_core.tools import tool
import requests
import os

# Credentials
NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_APP_KEY = os.getenv("NUTRITIONIX_APP_KEY")

BASE_URL = "https://trackapi.nutritionix.com/v2"

HEADERS = {
    "Content-Type": "application/json",
    "x-app-id": NUTRITIONIX_APP_ID,
    "x-app-key": NUTRITIONIX_APP_KEY
}

# 1️⃣ Instant Search Tool
@tool
def nutritionix_instant_search(query: str) -> dict:
    """
    Step 1: Search Nutritionix for foods by name.
    Returns only 2 unique common + 2 unique branded items.
    """
    try:
        resp = requests.get(f"{BASE_URL}/search/instant", headers=HEADERS, params={"query": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Filter common by tag_id
        seen_tag_ids = set()
        common_filtered = []
        for item in data.get("common", []):
            tag_id = item.get("tag_id")
            if tag_id and tag_id not in seen_tag_ids:
                seen_tag_ids.add(tag_id)
                common_filtered.append({
                    "food_name": item.get("food_name"),
                    "serving_unit": item.get("serving_unit"),
                    "serving_qty": item.get("serving_qty"),
                    "tag_id": tag_id,
                    "image": item.get("photo", {}).get("thumb")
                })
            if len(common_filtered) >= 2:
                break

        # Limit branded to 2
        branded_filtered = []
        for item in data.get("branded", []):
            branded_filtered.append({
                "food_name": item.get("food_name"),
                "brand_name": item.get("brand_name"),
                "serving_unit": item.get("serving_unit"),
                "serving_qty": item.get("serving_qty"),
                "calories": item.get("nf_calories"),
                "nix_item_id": item.get("nix_item_id"),
                "image": item.get("photo", {}).get("thumb")
            })
            if len(branded_filtered) >= 2:
                break

        return {"common": common_filtered, "branded": branded_filtered}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# 2️⃣ Item Details Tool
@tool
def nutritionix_item_details(nix_item_id: str) -> dict:
    """
    Step 2: Get full nutrition details for a branded food using nix_item_id.
    """
    try:
        resp = requests.get(f"{BASE_URL}/search/item", headers=HEADERS, params={"nix_item_id": nix_item_id}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("foods"):
            return {"error": "No details found."}

        item = data["foods"][0]
        return {
            "food_name": item.get("food_name"),
            "brand_name": item.get("brand_name"),
            "serving_size": f"{item.get('serving_qty')} {item.get('serving_unit')}",
            "calories": item.get("nf_calories"),
            "total_fat": item.get("nf_total_fat"),
            "sodium_mg": item.get("nf_sodium"),
            "carbohydrates": item.get("nf_total_carbohydrate"),
            "protein": item.get("nf_protein"),
            "ingredients": item.get("nf_ingredient_statement"),
            "image": item.get("photo", {}).get("thumb")
        }

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


tools = [search_tool,nutritionix_item_details,nutritionix_instant_search]
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

