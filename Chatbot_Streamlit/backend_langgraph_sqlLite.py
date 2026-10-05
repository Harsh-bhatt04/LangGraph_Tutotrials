from langgraph.graph import START, END, StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash-lite"
)


class ChatState(TypedDict):

    message: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):

    message_history = state['message']
    response = llm.invoke(message_history)

    return {'message': [response]}

graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

chatbot = graph.compile(checkpointer = checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)