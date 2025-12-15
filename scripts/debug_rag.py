
import logging
import sys
import os

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patching
from app.core.patch_chromadb import apply_chromadb_patch
apply_chromadb_patch()

from app.core.knowledge_base import KnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_rag():
    kb = KnowledgeBase()
    collection = kb.collection
    
    print(f"📚 Collection count: {collection.count()}")
    
    # Peek at first 5 items
    peek = collection.peek(limit=5)
    print("\n🔍 Peek (first 5):")
    for i in range(len(peek['ids'])):
        print(f"ID: {peek['ids'][i]}")
        print(f"Meta: {peek['metadatas'][i]}")
        print(f"Text: {peek['documents'][i][:200]}...") # Show first 200 chars
        print("-" * 40)
        
    query = "How to create task in billing portal"
    print(f"\n❓ Querying: '{query}'")
    
    results = collection.query(
        query_texts=[query],
        n_results=5
    )
    
    print("\n📉 Results:")
    if not results['ids'][0]:
        print("No results found.")
    
    for i in range(len(results['ids'][0])):
        doc_id = results['ids'][0][i]
        distance = results['distances'][0][i]
        document = results['documents'][0][i]
        metadata = results['metadatas'][0][i]
        
        print(f"Rank {i+1} (Dist: {distance:.4f}):")
        print(f"Source: {metadata.get('source')} (Slide/Page {metadata.get('slide_number') or metadata.get('page_number')})")
        print(f"Content: {document[:300]}...")
        print("-" * 40)

if __name__ == "__main__":
    debug_rag()
