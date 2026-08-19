from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import pymupdf
from langchain_core.documents import Document

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def load_pdf(path):
    doc = pymupdf.open(path)

    pages = []

    for page_number, page in enumerate(doc):
        text = page.get_text("text", sort=True)

        print(
            f"PAGE {page_number + 1}: "
            f"{len(text)} characters"
        )

        pages.append(
            Document(
                page_content=text,
                metadata={
                    "page": page_number + 1,
                    "source": str(path),
                },
            )
        )
    
    doc.close()

    return pages

class Ingestion():
    
    def embed(self, document):
        
        embeddings = model.encode(document)

        return embeddings
    
    def chunk_documents_with_embedding(self, documents, chunk_size, chunk_overlap):
        
        splitter = RecursiveCharacterTextSplitter(chunk_size= chunk_size, chunk_overlap = chunk_overlap)
        
        
        chunks = splitter.split_documents(documents)
        
        texts = [
            chunk.page_content
            for chunk in chunks
        ]
        
        embeddings = self.embed(texts)
        
        return embeddings, texts
        
