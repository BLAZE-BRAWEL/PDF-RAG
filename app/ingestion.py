from langchain_text_splitters import MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer
import pymupdf4llm
from .logger.logging import logger


model = SentenceTransformer("BAAI/bge-base-en-v1.5")

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
            embeddings = model.encode(document)
        
        except Exception:
            logger.exception("Failed to embed documents.")

        return embeddings
    
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
        
            embeddings = self.embed(texts)
        
        except Exception:
            logger.exception("Failed to chunk documents.")
            raise
        
        return embeddings, texts
        
