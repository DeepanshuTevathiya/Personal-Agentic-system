from app.memory.memory import create_embeddings, store_memory, retrieve_memories
from app.tools.health_tools import retrieve_health_data

# EMBEDDING MODEL TEST -------------------------------------------
# embedding = create_embeddings("I did bycep curl 30 minutes.")

# print(type(embedding))
# print(len(embedding))
# print(embedding[:5])

#EMBEDDING STORAGE TEST --------------------------------------------

# result = store_memory(
#     user_id=1,
#     source_type="workouts",
#     source_id=1,
#     content="User went running for 30 minutes."
# )
# print(result)

# RETRIEVE DATA TEST -------------------------------------------------
# result = retrieve_memories(
#     user_id=1,
#     query="What workout did I do recently?",
#     top_k=5
# )

# print(result)

# RETRIEVE DATA TEST--------------------------------------------------- 
result = retrieve_health_data.invoke(
    {
        "query": "What workouts did I do recently?",
        "user_id": 1
    }
)
print(result)