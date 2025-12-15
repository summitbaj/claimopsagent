
import os
import sys
import logging
from pathlib import Path
from typing import List

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INGEST_DIR = "data/ingest"
SUPPORTED_EXTENSIONS = {'.pdf', '.pptx', '.ppt', '.docx', '.doc'}

def get_files_to_ingest(directory: str) -> List[Path]:
    """Scan directory for supported files."""
    files = []
    path = Path(directory)
    
    if not path.exists():
        logger.warning(f"Directory {directory} does not exist. Creating it.")
        path.mkdir(parents=True, exist_ok=True)
        return []

    for item in path.glob('**/*'):
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(item)
            
    return files

def main():
    logger.info(f"Starting ingestion from {INGEST_DIR}")
    
    kb = KnowledgeBase()
    existing_sources = {s['filename'] for s in kb.get_uploaded_sources()}
    
    files = get_files_to_ingest(INGEST_DIR)
    
    if not files:
        logger.info("No supported files found to ingest.")
        return

    logger.info(f"Found {len(files)} files.")
    
    processed = 0
    skipped = 0
    errors = 0
    
    for file_path in files:
        filename = file_path.name
        
        if filename in existing_sources:
            logger.info(f"⏭️  Skipping {filename} (already exists)")
            skipped += 1
            continue
            
        logger.info(f"📥 Ingesting {filename}...")
        result = kb.ingest_file(str(file_path))
        
        if result.get("success"):
            logger.info(f"✅ Successfully ingested {filename}")
            processed += 1
        else:
            logger.error(f"❌ Failed to ingest {filename}: {result.get('error')}")
            errors += 1

    logger.info("-" * 40)
    logger.info(f"Ingestion complete.")
    logger.info(f"Processed: {processed}")
    logger.info(f"Skipped:   {skipped}")
    logger.info(f"Errors:    {errors}")

if __name__ == "__main__":
    main()
