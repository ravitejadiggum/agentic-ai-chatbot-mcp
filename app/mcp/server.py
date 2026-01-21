from mcp.server import Server
from mcp.server.stdio import stdio_server
import requests

server = Server("agentic-mcp-server")


@server.list_tools()
def list_tools():
    return [
        {
            "name": "weather",
            "description": "Get current weather for a city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        },
        {
            "name": "calculator",
            "description": "Evaluate a math expression",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    ]


@server.call_tool()
def call_tool(name: str, arguments: dict):
    if name == "weather":
        city = arguments["city"]
        return requests.get(f"https://wttr.in/{city}?format=3").text

    if name == "calculator":
        return str(eval(arguments["expression"]))

    raise ValueError(f"Unknown tool: {name}")


def main():
    stdio_server(server)


if __name__ == "__main__":
    main()
