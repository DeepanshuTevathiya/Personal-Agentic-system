from app.memory.memory import create_embeddings, store_memory

# EMBEDDING MODEL TEST -------------------------------------------
# embedding = create_embeddings("I did bycep curl 30 minutes.")

# print(type(embedding))
# print(len(embedding))
# print(embedding[:5])

#EMBEDDING STORAGE TEST --------------------------------------------

result = store_memory(
    user_id=1,
    source_type="workouts",
    source_id=1,
    content="User went running for 30 minutes."
)

print(result)