import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.graph import agent_graph
from app.agent.prompt import SYSTEM_PROMPT

load_dotenv()

def chat():
    print("Agentic AI Chatbot (type 'exit' to quit)")
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        messages.append(HumanMessage(content=user_input))
        result = agent_graph.invoke({"messages": messages})
        messages = result["messages"]

        print("AI:", messages[-1].content)

if __name__ == "__main__":
    chat()
