import streamlit as st
from backend_langgraph import chatbot
from langchain_core.messages import HumanMessage
import uuid

# Utility functions

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)

def load_converation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )

    return state.values.get("message", [])

def get_message_content(msg):
    content = msg.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text = ""

        for block in content:
            if isinstance(block, dict):
                text += block.get("text", "")

        return text

    return str(content)

# Session setup 
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_thread' not in st.session_state:
    st.session_state['chat_thread'] = []

add_thread(st.session_state['thread_id'])

# Sidebar design for UI
st.sidebar.title("LangGraph chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My conversations")

for thread_id in st.session_state['chat_thread'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_converation(thread_id)

        temp_message = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_message.append({'role': role, "content" : get_message_content(msg)})
            
        st.session_state['message_history'] = temp_message
            

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
                {'message': [HumanMessage(content=user_input)]},
                config={'configurable': {'thread_id': st.session_state['thread_id']}},
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
