
import os
import logging
import pydantic
import pydantic_settings

logger = logging.getLogger(__name__)

def apply_chromadb_patch():
    """
    Apply monkey patches to make ChromaDB 0.3.23 compatible with Pydantic V2.
    This fixes:
    1. BaseSettings location compatibility.
    2. Private attribute handling in Collection instances (_client, _embedding_function).
    """
    logger.info("🔧 Applying ChromaDB v0.3.23 + Pydantic V2 Compatibility Patch")

    # 1. Patch BaseSettings
    class PatchedBaseSettings(pydantic_settings.BaseSettings):
        model_config = pydantic_settings.SettingsConfigDict(extra="ignore")

    # Inject dummy values for defaults
    start_defaults = {
        "CLICKHOUSE_HOST": "localhost",
        "CLICKHOUSE_PORT": "8123",
        "CHROMA_SERVER_HOST": "localhost",
        "CHROMA_SERVER_HTTP_PORT": "8000",
        "CHROMA_SERVER_GRPC_PORT": "50051"
    }
    for key, val in start_defaults.items():
        if key not in os.environ:
            os.environ[key] = val

    pydantic.BaseSettings = PatchedBaseSettings
    
    # 2. Monkey Patch Collection.__init__
    # Pydantic V2 models don't auto-store private attributes if they aren't fields.
    # We must explicitly force them into __pydantic_private__.
    
    # Delayed import to allow BaseSettings patch to take effect first
    import chromadb.api.models.Collection
    from chromadb.api.models.Collection import Collection

    if hasattr(Collection, '_patched_for_v2'):
        logger.info("✅ Collection already patched.")
        return

    original_init = Collection.__init__

    def new_init(self, client, name, id, embedding_function=None, metadata=None):
        original_init(self, client, name, id, embedding_function, metadata)
        
        # Initialize __pydantic_private__ if missing
        if getattr(self, '__pydantic_private__', None) is None:
            object.__setattr__(self, '__pydantic_private__', {})
            
        self.__pydantic_private__['_client'] = client
        self.__pydantic_private__['_embedding_function'] = embedding_function

    Collection.__init__ = new_init
    Collection._patched_for_v2 = True
    logger.info("✅ Applied Collection.__init__ monkey patch")
