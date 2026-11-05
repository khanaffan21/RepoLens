from functools import lru_cache
from sentence_transformers import SentenceTransformer
from ..config import settings
@lru_cache
def get_model(): return SentenceTransformer(settings.embedding_model)
def embed(texts):
    if not texts:return []
    return get_model().encode(texts,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False).tolist()
