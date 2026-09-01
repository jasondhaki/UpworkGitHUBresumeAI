from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer("all-MiniLM-L6-v2")

pairs = [
    ("Pinecone", "vector database"),
    ("Pinecone", "relational database"),
    ("PyTorch", "deep learning framework"),
    ("PyTorch", "spreadsheet software"),
    ("Experience with Pinecone", "vector database experience"),
    ("Experience with Pinecone", "relational database experience"),
    ("Built a RAG pipeline using Pinecone for retrieval", "vector database"),
    ("Built a RAG pipeline using Pinecone for retrieval", "relational database"),
]

for a, b in pairs:
    emb = model.encode([a, b])
    sim = cos_sim(emb[0], emb[1]).item()
    print(f"{a!r:12} vs {b!r:28} -> {sim:.3f}")
