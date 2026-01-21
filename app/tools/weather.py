import requests
from langchain.tools import tool

@tool
def weather(city: str) -> str:
    """Get current weather for a city."""
    url = f"https://wttr.in/{city}?format=3"
    return requests.get(url).text
