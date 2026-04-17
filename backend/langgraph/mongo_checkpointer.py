from langgraph.checkpoint.memory import MemorySaver

def get_mongo_checkpointer():
    """Use MemorySaver to avoid import issues"""
    return MemorySaver()