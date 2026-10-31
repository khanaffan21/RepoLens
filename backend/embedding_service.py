from sentence_transformers import SentenceTransformer


# Embedding model configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:

    def __init__(self):
        print("Loading embedding model...")

        self.model = SentenceTransformer(MODEL_NAME)

        print("Embedding model loaded successfully!")

    def generate_embedding(self, text: str):
        """
        Convert a single text into a numerical vector.
        """

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embedding.tolist()

    def generate_embeddings(self, texts: list[str]):
        """
        Convert multiple text chunks into numerical vectors.
        """

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return embeddings.tolist()


# Create a reusable embedding service
embedding_service = EmbeddingService()