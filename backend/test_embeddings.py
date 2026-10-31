from embedding_service import embedding_service


# Sample code snippets
code_samples = [
    "def login(username, password): return authenticate(username, password)",

    "def connect_database(): return database_connection()",

    "def calculate_sum(a, b): return a + b"
]


print("\nGenerating embeddings...\n")

embeddings = embedding_service.generate_embeddings(code_samples)


print("\n========== EMBEDDING RESULTS ==========")

print("Total embeddings:", len(embeddings))

for index, embedding in enumerate(embeddings):

    print(f"\nCode Sample {index + 1}")
    print("Vector dimensions:", len(embedding))
    print("First 5 values:", embedding[:5])