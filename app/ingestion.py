from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer
import pymupdf4llm
from langchain_core.documents import Document

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def load_pdf(path):
    doc = pymupdf4llm.to_markdown(path)

    pdf_text = doc
    
    
    return pdf_text

class Ingestion():
    
    def embed(self, document):
        
        embeddings = model.encode(document)

        return embeddings
    
    def chunk_documents_with_embedding(self, document, chunk_size, chunk_overlap):
        
        
        splitter_headers = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3")
        ]
        
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on= splitter_headers
        )
        
        
        chunks = splitter.split_text(document)
        
        
        texts = [
            chunk.page_content
            for chunk in chunks
        ]
        
        embeddings = self.embed(texts)
        
        
        return embeddings, texts
        
