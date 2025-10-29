# Sources/Embedder.py
import os
import numpy as np
from typing import Optional
from google import genai
from google.genai.types import EmbedContentConfig
import logging

class Embedder:
    def __init__(
        self,
        modelName: str = "models/gemini-embedding-001",
        apiKey: Optional[str] = None, #"",
        dimensions: int = 3072
    ):
        self.model      = modelName
        self.apiKey     = os.getenv("GEMINI_KEY")
        self.dimensions = dimensions

        logging.info(f"Embedder initialized with model: {self.model}")
        
    def Encode(self, texts, batchSize: int = 64, normalize: bool = True) -> np.ndarray:
        logging.info(f"Embedding {len(texts)} texts in batches of {batchSize}...")

        if not texts:
            return np.zeros((0, self.dimensions), dtype = np.float32)

        embeddingValues = []
        config = EmbedContentConfig(task_type = "SEMANTIC_SIMILARITY", output_dimensionality = self.dimensions)
        with genai.Client(api_key = self.apiKey) as aiClient:
            try:
                for i in range(0, len(texts), batchSize):
                    batch = texts[i : i + batchSize]
                    response = aiClient.models.embed_content(model = self.model, contents = batch, config = config)
                    embeddingValues.extend(e.values for e in response.embeddings)
            except Exception as e:
                    logging.error(f"An error occurred during embedding a batch: {e}")

        embeddings = np.array(embeddingValues, dtype = np.float32)

        if normalize and embeddings.size > 0:
            norms = np.linalg.norm(embeddings, axis = 1, keepdims = True)
            embeddings /= (norms + 1e-9)
        logging.info(f"Successfully created {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}.")

        return embeddings
