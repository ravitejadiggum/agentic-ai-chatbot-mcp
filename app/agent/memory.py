import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Single Chroma client (persistent)
_client = chromadb.Client(
    Settings(
        persist_directory="./chroma",
        anonymized_telemetry=False
    )
)

# Default embedding function (local, no API key needed)
_embedding_fn = embedding_functions.DefaultEmbeddingFunction()

def get_memory_collection():
    """
    Returns a persistent Chroma collection for chat memory.
    """
    collection = _client.get_or_create_collection(
        name="agentic_chat_memory",
        embedding_function=_embedding_fn
    )
    return collection
