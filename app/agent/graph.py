from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.agent.prompt import SYSTEM_PROMPT



# LLM

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)



# TOOL INPUT SCHEMAS (ONLY SCHEMAS, NO EXECUTION)

class WeatherInput(BaseModel):
    city: str


class CalculatorInput(BaseModel):
    expression: str



# TOOL DEFINITIONS (SCHEMA ONLY – MCP EXECUTES THEM)

weather_tool = StructuredTool(
    name="weather",
    description="Get current weather conditions of a city like Bangalore, Delhi, London",
    args_schema=WeatherInput,
    func=lambda **kwargs: None
)

calculator_tool = StructuredTool(
    name="calculator",
    description="ONLY for arithmetic math like 2+2, 10*5, 100/4",
    args_schema=CalculatorInput,
    func=lambda **kwargs: None
)

tools = [weather_tool, calculator_tool]

# Bind tool schemas to LLM
llm_with_tools = llm.bind_tools(tools)


# STATE

class AgentState(TypedDict):
    messages: List[BaseMessage]



# AGENT NODE (DECIDES: TOOL OR DIRECT ANSWER)

def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}



# TOOL NODE (PLACEHOLDER – REAL EXECUTION HAPPENS IN agent_runner.py)

def tool_node(state: AgentState):
    """
    This node exists ONLY to satisfy LangGraph flow.
    Actual tool execution happens in agent_runner via MCP.
    """
    last_message = state["messages"][-1]

    # Return tool call info as-is
    tool_messages = [
        ToolMessage(
            content="Tool execution delegated to MCP",
            tool_call_id=call["id"]
        )
        for call in last_message.tool_calls
    ]

    return {"messages": state["messages"] + tool_messages}



# ROUTER

def should_use_tool(state: AgentState):
    last = state["messages"][-1]
    return "tool" if getattr(last, "tool_calls", None) else END



# GRAPH

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tool", tool_node)

graph.set_entry_point("agent")
graph.add_conditional_edges(
    "agent",
    should_use_tool,
    {"tool": "tool", END: END}
)

graph.add_edge("tool", "agent")

agent_graph = graph.compile()   