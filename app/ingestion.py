from langchain_text_splitters import MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer
import pymupdf4llm
from .logger.logging import logger
from fastembed import SparseTextEmbedding

dense_model = SentenceTransformer("BAAI/bge-base-en-v1.5")

sparse_model = SparseTextEmbedding(
    model_name="prithivida/Splade_PP_en_v1"
)

def load_pdf(path):
    try:
        doc = pymupdf4llm.to_markdown(path)

        pdf_text = doc
    
    except Exception:
        
        logger.exception("Failed to load PDF.")
        
        raise
    
    
    return pdf_text

class Ingestion():
    
    def embed(self, document):
        
        try:
            dense_embeddings = dense_model.encode(document)
            sparse_embeddings = list(sparse_model.embed(document))
        
        except Exception:
            logger.exception("Failed to embed documents.")

        return dense_embeddings, sparse_embeddings
    
    def chunk_documents_with_embedding(self, document):
        
        
        splitter_headers = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3")
        ]
        
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on= splitter_headers
        )
        
        
        try :
            chunks = splitter.split_text(document)
        
        
            texts = [
                chunk.page_content
                for chunk in chunks
            ]
        
            dense_embedding, sparse_embedding = self.embed(texts)
        
        except Exception:
            logger.exception("Failed to chunk documents.")
            raise
        
        return dense_embedding, sparse_embedding, texts
        
