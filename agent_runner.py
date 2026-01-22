import sys
import json
import traceback

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.agent.graph import agent_graph
from app.agent.prompt import SYSTEM_PROMPT
from app.mcp.client import MCPClient



# GUARDRAIL HELPERS
#working


def is_greeting(text: str) -> bool:
    return text.lower().strip() in ["hi", "hello", "hey", "good morning", "good evening"]


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

    if len(text.strip()) < 15:
        return True

    return any(p in text.lower() for p in weak_phrases)


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



# TOOL OUTPUT FORMATTER


def format_weather_output(raw: str) -> str:
    """
    Converts raw JSON weather data into a clean human-readable response
    """
    try:
        data = json.loads(raw)

        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})

        return (
            f"🌤️ Weather Update\n\n"
            f"• Temperature: {main.get('temp')}°C\n"
            f"• Feels Like: {main.get('feels_like')}°C\n"
            f"• Condition: {weather.get('description', '').title()}\n"
            f"• Humidity: {main.get('humidity')}%\n"
            f"• Wind Speed: {wind.get('speed')} m/s"
        )

    except Exception:
        # If parsing fails, return raw safely
        return raw



# AGENT RUNNER


def main():
    MCPClient()  # ensure MCP server connection

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                continue

            data = json.loads(line)
            user_input = data.get("message", "").strip()

            messages.append(HumanMessage(content=user_input))

            result = agent_graph.invoke({"messages": messages})
            messages = result["messages"]
            last_message = messages[-1]

            response_text = last_message.content

            # Guardrail retry ONLY for LLM text
            if (
                not is_greeting(user_input)
                and not isinstance(last_message, ToolMessage)
                and is_weak_response(response_text)
            ):
                messages = retry_with_stronger_prompt(messages)
                result = agent_graph.invoke({"messages": messages})
                messages = result["messages"]
                last_message = messages[-1]
                response_text = last_message.content

            #FORMAT TOOL OUTPUT
            if isinstance(last_message, ToolMessage):
                response_text = format_weather_output(response_text)

           
            # STREAM RESPONSE
            

            CHUNK_SIZE = 20
            for i in range(0, len(response_text), CHUNK_SIZE):
                print(json.dumps({"stream": response_text[i:i + CHUNK_SIZE]}), flush=True)

            print(json.dumps({"end": True}), flush=True)

        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
