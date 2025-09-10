import streamlit as st
from backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid
from datetime import datetime

# **************************************** Utility Functions *************************

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    """Start a new thread and reset its message history + tool log."""
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []
    st.session_state['tool_log'][thread_id] = []  # reset tool log for new thread

def add_thread(thread_id):
    """Ensure thread exists in chat_threads and tool_log."""
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
    if thread_id not in st.session_state['tool_log']:
        st.session_state['tool_log'][thread_id] = []

def load_conversation(thread_id):
    """Load stored conversation from backend for a given thread."""
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

def log_tool_usage(thread_id, tool_name: str):
    """Append a tool usage record with timestamp for the given thread."""
    if 'tool_log' not in st.session_state:
        st.session_state['tool_log'] = {}
    if thread_id not in st.session_state['tool_log']:
        st.session_state['tool_log'][thread_id] = []
    st.session_state['tool_log'][thread_id].append({
        "tool": tool_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'tool_log' not in st.session_state:
    st.session_state['tool_log'] = {}

add_thread(st.session_state['thread_id'])

# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages

# Tool usage log display (thread‑specific)
st.sidebar.subheader("🛠 Tool Usage Log")
current_thread_log = st.session_state['tool_log'].get(st.session_state['thread_id'], [])
if current_thread_log:
    for entry in reversed(current_thread_log):
        st.sidebar.write(f"{entry['timestamp']} — `{entry['tool']}`")
else:
    st.sidebar.write("No tools used yet.")

# **************************************** Chat Display *******************************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    # Add user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # Assistant streaming block
    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},  # type: ignore
                config=CONFIG,  # type: ignore
                stream_mode="messages",
            ):
                # Detect tool usage
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    log_tool_usage(st.session_state['thread_id'], tool_name)

                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(  # type: ignore
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream assistant tokens
                if isinstance(message_chunk, AIMessage):
                    text = message_chunk.content
                    # Normalize to string
                    if isinstance(text, list):
                        # Extract only text parts if structured
                        text = "".join(
                            part.get("text", "")
                            for part in text
                            if isinstance(part, dict) and part.get("type") == "text"
                        )
                    elif not isinstance(text, str):
                        text = str(text)
                    if text:
                        yield text

        ai_message = st.write_stream(ai_only_stream())

        # Finalize tool status if used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    # Save assistant message
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )
