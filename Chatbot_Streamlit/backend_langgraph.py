from langgraph.graph import START, END, StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv


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

checkpointer = InMemorySaver()

chatbot = graph.compile(checkpointer = checkpointer)
