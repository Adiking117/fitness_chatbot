from langchain_groq import ChatGroq
from config.env import GROQ_MODEL

llm = ChatGroq(model=GROQ_MODEL)
