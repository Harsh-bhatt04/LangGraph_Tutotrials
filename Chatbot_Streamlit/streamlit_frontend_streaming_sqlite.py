import streamlit as st
from backend_langgraph_tool import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# Utility functions

def generate_thread_id():
    # Convert to string to avoid serialization/comparison mismatch with DB
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []
    st.rerun() # Force Streamlit to refresh the UI immediately

def add_thread(thread_id):
    # Ensure thread_id is a string when storing/checking
    t_id_str = str(thread_id)
    if t_id_str not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(t_id_str)

def load_converation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': str(thread_id)}}
    )
    # FIX: Changed "message" to "messages" to match your graph's ChatState
    return state.values.get("messages", [])

def get_message_content(msg):
    content = msg.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text = ""
        for block in content:
            if isinstance(block, dict):
                text += block.get("text", "")
            elif isinstance(block, str):
                text += block
        return text

    return str(content)

# Session setup 
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_thread' not in st.session_state:
    # Ensure all thread IDs fetched from the database are processed as strings
    st.session_state['chat_thread'] = [str(t) for t in retrieve_all_threads()]

add_thread(st.session_state['thread_id'])

# Sidebar design for UI
st.sidebar.title("LangGraph chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My conversations")

for thread_id in st.session_state['chat_thread'][::-1]:
    # Highlight the currently active thread in the sidebar
    label = f"💬 {thread_id[:8]}..." if thread_id == st.session_state['thread_id'] else f" {thread_id[:8]}..."
    
    if st.sidebar.button(label, key=f"btn_{thread_id}"):
        st.session_state['thread_id'] = thread_id
        messages = load_converation(thread_id)

        temp_message = []
        for msg in messages:
            # Skip empty AI messages or system tool call wrappers to avoid blank boxes
            if not msg.content and hasattr(msg, 'tool_calls') and msg.tool_calls:
                continue
            if hasattr(msg, 'type') and msg.type == 'tool':
                continue
                
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            
            content_str = get_message_content(msg)
            if content_str.strip(): # Only add if there is text
                temp_message.append({'role': role, "content" : content_str})
            
        st.session_state['message_history'] = temp_message
        st.rerun() # FIX: Force page redraw so the main window displays the loaded history right away
            

# loading conversation history 
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])


user_input = st.chat_input('Type Here')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    with st.chat_message('assistant'):
        def stream_response():
            # Use stream_mode="messages" to get token chunks as they stream out
            for chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config={'configurable': {'thread_id': st.session_state['thread_id']},
                        'metadata': {'thread_id': st.session_state['thread_id']},
                        'run_name': 'Chat Run'
                        },
                stream_mode='messages'
            ):
                # Ensure the token chunk comes from our chat node text generation
                if metadata.get('langgraph_node') == 'chat_node':
                    content = chunk.content
                    
                    # Handle Gemini's string chunks or block lists
                    if isinstance(content, str):
                        yield content
                    elif isinstance(content, list) and len(content) > 0:
                        text = content[0].get('text', '') if isinstance(content[0], dict) else ''
                        yield text

        # st.write_stream will now animate the text word-by-word perfectly
        ai_message = st.write_stream(stream_response())
    
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
