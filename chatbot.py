from langgraph.graph import START, END, StateGraph
from typing import TypedDict, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import tool, DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import asyncio

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}

tools = [calculator]

llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):

    messages: Annotated[list[str], add_messages]


def build_graph():

    async def chat_node(state: ChatState):

        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {'messages': [response]}

    tool_node = ToolNode(tools)

    # defining graph and nodes
    graph = StateGraph(ChatState)

    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    # defining graph connections
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")

    chatbot = graph.compile()

    return chatbot

async def main():

    chatbot = build_graph()

    # running the graph
    result = await chatbot.ainvoke({"messages": [HumanMessage(content="Find the modulus of 132354 and 23 and give answer like a cricket commentator.")]})

    print(result['messages'][-1].text)

if main == '__main__':
    asyncio.run(main())