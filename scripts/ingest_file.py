
import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- PYDANTIC V2 COMPATIBILITY PATCH START ---
from app.core.patch_chromadb import apply_chromadb_patch
apply_chromadb_patch()
# --- PYDANTIC V2 COMPATIBILITY PATCH END ---

from app.core.knowledge_base import KnowledgeBase

def main():
    parser = argparse.ArgumentParser(description="Ingest a file into the ClaimsOps Knowledge Base")
    parser.add_argument("file_path", help="Path to the file to ingest (.pdf, .pptx, .docx)")
    args = parser.parse_args()

    file_path = Path(args.file_path)
    
    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}")
        return

    logger.info(f"📥 Ingesting {file_path}...")
    
    kb = KnowledgeBase()
    
    # Check if already exists (optional but good)
    existing_sources = {s['filename'] for s in kb.get_uploaded_sources()}
    if file_path.name in existing_sources:
        logger.warning(f"⚠️  Warning: {file_path.name} is already in the knowledge base. Re-ingesting will add duplicate chunks unless handled by ID.")

    result = kb.ingest_file(str(file_path))
    
    if result.get("success"):
        logger.info("-" * 40)
        logger.info(f"✅ Successfully ingested {file_path.name}")
        logger.info(f"   Chunks created: {result.get('chunks_created')}")
        logger.info(f"   Units processed: {result.get('units_processed')}")
        logger.info("-" * 40)
    else:
        logger.error("-" * 40)
        logger.error(f"❌ Failed to ingest {file_path.name}")
        logger.error(f"   Error: {result.get('error')}")
        logger.error("-" * 40)

if __name__ == "__main__":
    main()
