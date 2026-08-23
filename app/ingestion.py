from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import pymupdf
from langchain_core.documents import Document

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def load_pdf(path):
    doc = pymupdf.open(path)

    pages = []

    for page in doc:
        text = page.get_text("text", sort=True)


        pages.append(text)
    
    doc.close()

    pdf_text = " ".join(page for page in pages)
    
    document = Document(
        page_content = pdf_text,
        metadata = {
            "source" : str(path)
        }
    )
    
    return document

class Ingestion():
    
    def embed(self, document):
        
        embeddings = model.encode(document)

        return embeddings
    
    def chunk_documents_with_embedding(self, document, chunk_size, chunk_overlap):
        
        splitter = RecursiveCharacterTextSplitter(chunk_size= chunk_size, chunk_overlap = chunk_overlap)
        
        
        chunks = splitter.split_documents([document])
        
        
        texts = [
            chunk.page_content
            for chunk in chunks
        ]
        
        embeddings = self.embed(texts)
        
        
        return embeddings, texts
        
