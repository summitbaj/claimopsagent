
import os
import logging
from pathlib import Path
from typing import List, Set
from app.core.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

def run_auto_ingest(folder_path: str = "data/ingest"):
    """
    Scans the specified folder and ingests any supported files that are not
    already present in the Knowledge Base.
    """
    ingest_dir = Path(folder_path)
    
    # Create directory if it doesn't exist
    if not ingest_dir.exists():
        logger.info(f"📂 Creating auto-ingest directory: {ingest_dir}")
        ingest_dir.mkdir(parents=True, exist_ok=True)
        return

    # List supported files
    supported_extensions = {'.pptx', '.ppt', '.pdf', '.docx', '.doc'}
    files_to_check = [
        f for f in ingest_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]
    
    if not files_to_check:
        logger.info(f"📂 Auto-ingest folder {folder_path} is empty or has no supported files.")
        return

    logger.info(f"🔎 Scanning {len(files_to_check)} files in {folder_path} for auto-ingestion...")

    try:
        kb = KnowledgeBase()
        sources = kb.get_uploaded_sources()
        existing_filenames: Set[str] = {s['filename'] for s in sources}
        
        new_files_count = 0
        
        for file_path in files_to_check:
            if file_path.name in existing_filenames:
                logger.debug(f"⏭️  Skipping existing file: {file_path.name}")
                continue
            
            logger.info(f"📥 Auto-ingesting new file: {file_path.name}...")
            result = kb.ingest_file(str(file_path))
            
            if result.get("success"):
                logger.info(f"✅ Successfully ingested {file_path.name}")
                new_files_count += 1
            else:
                logger.error(f"❌ Failed to ingest {file_path.name}: {result.get('error')}")
                
        if new_files_count > 0:
            logger.info(f"🎉 Auto-ingestion complete. Added {new_files_count} new files.")
        else:
            logger.info("✨ No new files to ingest.")
            
    except Exception as e:
        logger.error(f"❌ Error during auto-ingestion: {str(e)}", exc_info=True)
