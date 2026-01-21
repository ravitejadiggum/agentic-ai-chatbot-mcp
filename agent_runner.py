import sys
import json
import traceback

from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.graph import agent_graph
from app.agent.prompt import SYSTEM_PROMPT
from app.mcp.client import MCPClient


# -------------------------------------------------
# 🛡 GUARDRAIL HELPERS
# -------------------------------------------------
def is_greeting(text: str) -> bool:
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]
    return text.lower().strip() in greetings


def is_weak_response(text: str) -> bool:
    weak_phrases = [
        "i'm not sure",
        "i am not sure",
        "i don't know",
        "i do not know",
        "as an ai",
        "cannot answer",
        "not sure"
    ]

    text_lower = text.lower()

    if len(text.strip()) < 15:
        return True

    return any(phrase in text_lower for phrase in weak_phrases)


def retry_with_stronger_prompt(messages):
    messages.insert(
        1,
        SystemMessage(
            content=(
                "Answer confidently and clearly. "
                "Do not say you are unsure. "
                "Provide a direct, factual, and helpful response."
            )
        )
    )
    return messages


# -------------------------------------------------
# AGENT RUNNER
# -------------------------------------------------
def main():
    mcp_client = MCPClient()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                continue

            data = json.loads(line)
            user_input = data.get("message", "").strip()

            messages.append(HumanMessage(content=user_input))

            # First LLM call
            result = agent_graph.invoke({"messages": messages})
            messages = result["messages"]
            response_text = messages[-1].content

            # 🛡 Guardrail (ONLY if meaningful question)
            if (
                not is_greeting(user_input)
                and is_weak_response(response_text)
            ):
                messages = retry_with_stronger_prompt(messages)
                result = agent_graph.invoke({"messages": messages})
                messages = result["messages"]
                response_text = messages[-1].content

            # -------------------------------------------------
            # STREAM RESPONSE
            # -------------------------------------------------
            CHUNK_SIZE = 20

            for i in range(0, len(response_text), CHUNK_SIZE):
                chunk = response_text[i:i + CHUNK_SIZE]
                print(json.dumps({"stream": chunk}), flush=True)

            print(json.dumps({"end": True}), flush=True)

        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
