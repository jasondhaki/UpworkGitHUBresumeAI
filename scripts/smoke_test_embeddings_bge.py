from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def score(query, candidates):
    q = "Represent this sentence for searching relevant passages: " + query
    qemb = model.encode([q])
    cembs = model.encode(candidates)
    for c, cemb in zip(candidates, cembs):
        print(f"  {query!r:50} vs {c!r:24} -> {cos_sim(qemb[0], cemb).item():.3f}")

score("Pinecone", ["vector database", "relational database"])
score("Experience with Pinecone", ["vector database experience", "relational database experience"])
score("Built a RAG pipeline using Pinecone for retrieval", ["vector database", "relational database"])
score("PyTorch", ["deep learning framework", "spreadsheet software"])
