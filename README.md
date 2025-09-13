# 🧑‍⚕️ Nutrition + Fitness Chatbot (LangGraph + Streamlit)

An interactive chatbot powered by **LangGraph**, **Streamlit**, and the **Nutritionix API** that can:

- Answer general questions using DuckDuckGo search  
- Fetch nutrition details for foods (calories, macros, etc.)  
- Estimate calories burned from exercises  
- Maintain chat threads (saved with SQLite)  
- Provide tool usage logs (so you know when APIs were used)  

---

## 🚀 Features
- LLM-powered chat with **Groq LLaMA-3.1 (llama-3.1-8b-instant)**  
- **DuckDuckGo Search** integration for real-time information  
- **Nutritionix API** for food & exercise data  
- **SQLite checkpointing** to persist conversations  
- Multiple conversation threads — revisit past chats easily  
- Tool usage log with timestamps  
- **Streamlit frontend** with chat UI + sidebar navigation  

---

## 📂 Project Structure
```
.
├── .gitignore
├── .python-version
├── backend.py
├── chatbot.db
├── frontend.py
├── main.py
├── pyproject.toml
├── README.md
├── uv.lock
├── config
│   └── env.py
├── db
│   └── checkpoint.py
├── graph
│   ├── build_graph.py
│   ├── nodes.py
│   └── state.py
├── llm
│   └── groq_llm.py
├── tools
│   ├── nutritionix.py
│   └── search.py
└── utils
    └── threads.py

```

---

## ⚙️ Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/nutrition-fitness-chatbot.git
cd nutrition-fitness-chatbot
```

### 2. Create virtual environment & install dependencies
```bash
python -m venv venv
source venv/bin/activate    # Linux / Mac
venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the project root (use `.env.example` as a reference):

```ini
# Nutritionix API
NUTRITIONIX_APP_ID=your_app_id
NUTRITIONIX_APP_KEY=your_app_key

# (Optional) Groq API key
GROQ_API_KEY=your_groq_api_key
```

🔑 Get Nutritionix credentials here → https://developer.nutritionix.com/  

### 4. Run the app
```bash
streamlit run frontend.py
```

Your chatbot will be live at → [http://localhost:8501](http://localhost:8501) 🎉  

---

## 🧩 How It Works

### 1. Backend (`backend.py`)
- Loads LLM (Groq + LLaMA-3.1)  
- Defines tools:
  - DuckDuckGo search  
  - Nutritionix food + exercise queries  
- Saves conversations + tool logs in SQLite  

### 2. Frontend (`frontend.py`)
- Built with Streamlit chat UI (`st.chat_message`, `st.chat_input`)  
- Sidebar lets you:
  - Start a new chat  
  - Switch between saved threads  
  - View tool usage logs  
- Streams responses live  

### 3. Threads & Persistence
- Stored in **SQLite (`chatbot.db`)**  
- Each thread has a **UUID**  
- Can revisit old chats anytime  

---

## 📊 Example Usage

**User:**  
```
How many calories are in 2 bananas?
```
**Bot (via Nutritionix):**  
```
2 bananas (~242g) → 210 kcal, 1g protein, 54g carbs, 0.7g fat
```

**User:**  
```
I did 30 mins running, how many calories did I burn?
```
**Bot (via Nutritionix Exercise):**  
```
Running (30 min, ~8 km/h) → ~300 kcal burned
```

**User:**  
```
Who is the CEO of OpenAI?
```
**Bot (via DuckDuckGo):**  
```
The current CEO of OpenAI is Sam Altman.
```

---

## ✅ Future Improvements
- Add **user authentication** (per-user threads)  
- Enhance UI with **charts for nutrition breakdown**  
- Add **caching** for faster responses  
- Deploy via **Streamlit Cloud** or **Docker**  

---

## 🤝 Contributing
1. Fork repo  
2. Create a feature branch → `git checkout -b feature/xyz`  
3. Commit changes → `git commit -m "Add feature xyz"`  
4. Push branch & open PR  

---

## 📜 License
MIT License © 2025 Aditya Choudhari
