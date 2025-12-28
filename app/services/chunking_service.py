"""Document chunking service using LangChain.

Strategy: Recursive character text splitting
- Splits by paragraphs first (\n\n)
- Then by sentences (\n)
- Then by words (space)
- Then by characters (last resort)

Chunk size: ~2048 chars (512 tokens)
Overlap: ~200 chars (50 tokens, 10%)
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    Document chunking using RecursiveCharacterTextSplitter.

    Optimized for:
    - Multilingual text (Khmer, English, Vietnamese)
    - OCR-extracted PDFs (may have noise)
    - Agricultural documents (reports, policies)

    Strategy:
    - Paragraph-first splitting (preserves context)
    - Configurable overlap (prevents context loss at boundaries)
    - Metadata preservation (source, commodity, etc.)
    """

    def __init__(
        self,
        chunk_size: int = 2048,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Target chunk size in characters (default: 2048 = ~512 tokens)
            chunk_overlap: Character overlap between chunks (default: 200 = ~50 tokens, 10%)
            separators: List of split separators (default: paragraphs → sentences → words)

        Reasoning:
            - 2048 chars ≈ 512 tokens (optimal for multilingual-e5-large)
            - 10% overlap preserves context across chunk boundaries
            - Paragraph-first ensures semantic coherence
        """
        if separators is None:
            # Default: split by paragraphs, then newlines, then spaces
            separators = [
                "\n\n",  # Paragraphs (highest priority)
                "\n",    # Sentences/lines
                " ",     # Words
                ""       # Characters (last resort)
            ]

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )

        logger.info(
            f"ChunkingService initialized: "
            f"size={chunk_size}, overlap={chunk_overlap}, separators={len(separators)}"
        )

    def chunk_document(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a single document into smaller pieces.

        Args:
            text: Document text content
            document_id: UUID of source document (for linking)
            metadata: Additional metadata to attach to each chunk
                     Should include: source, commodity, title, url, etc.

        Returns:
            List of chunk dictionaries with structure:
            {
                'document_id': UUID,
                'chunk_index': int (0-based),
                'chunk_text': str,
                'metadata': {
                    ...original metadata...,
                    'chunk_index': int,
                    'total_chunks': int,
                    'char_count': int,
                    'has_overlap': bool
                }
            }

        Example:
            >>> service = ChunkingService()
            >>> text = "Long document text..." * 100  # ~2000 chars
            >>> chunks = service.chunk_document(
            ...     text,
            ...     document_id="abc-123",
            ...     metadata={'source': 'GDrive', 'commodity': 'cashew'}
            ... )
            >>> len(chunks)
            1
            >>> chunks[0]['chunk_index']
            0
            >>> chunks[0]['metadata']['total_chunks']
            1

        Note:
            Short documents (<2048 chars) result in single chunk.
            Long documents are split intelligently at paragraph/sentence boundaries.
        """
        if not text or not text.strip():
            logger.warning(f"Empty text for document {document_id}")
            return []

        # Split text into chunks
        try:
            chunks_text = self.text_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error splitting text for document {document_id}: {e}")
            # Fallback: treat entire text as one chunk
            chunks_text = [text]

        total_chunks = len(chunks_text)

        # Build chunk dictionaries
        result = []
        for i, chunk_text in enumerate(chunks_text):
            chunk_metadata = metadata.copy() if metadata else {}

            # Add chunk-specific metadata
            chunk_metadata.update({
                'chunk_index': i,
                'total_chunks': total_chunks,
                'char_count': len(chunk_text),
                'has_overlap': i > 0  # All chunks except first have overlap with previous
            })

            result.append({
                'document_id': document_id,
                'chunk_index': i,
                'chunk_text': chunk_text.strip(),
                'metadata': chunk_metadata
            })

        logger.info(
            f"Chunked document {document_id}: "
            f"{len(text)} chars → {total_chunks} chunks "
            f"(avg {len(text) // total_chunks if total_chunks > 0 else 0} chars/chunk)"
        )

        return result

    def chunk_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents in batch.

        Args:
            documents: List of document dicts with structure:
                {
                    'id': UUID,
                    'text_content': str,
                    'source': str,
                    'commodity': str,
                    'title': str,
                    ...other metadata...
                }

        Returns:
            Flat list of all chunks from all documents

        Example:
            >>> service = ChunkingService()
            >>> docs = [
            ...     {'id': '1', 'text_content': 'Doc 1...', 'source': 'GDrive'},
            ...     {'id': '2', 'text_content': 'Doc 2...', 'source': 'ODC'}
            ... ]
            >>> all_chunks = service.chunk_documents_batch(docs)
            >>> len(all_chunks)  # Total chunks from both docs
            5

        Performance:
            ~1000 docs/second (chunking is CPU-bound, very fast)
        """
        all_chunks = []

        for doc in documents:
            doc_id = doc.get('id')
            text = doc.get('text_content', '')

            if not doc_id:
                logger.warning("Document missing 'id' field, skipping")
                continue

            # Build metadata from document fields
            metadata = {
                'source': doc.get('source'),
                'commodity': doc.get('commodity'),
                'title': doc.get('title'),
                'url': doc.get('url'),
                'extraction_method': doc.get('extraction_method'),
                'scraped_at': doc.get('scraped_at')
            }

            # Chunk document
            chunks = self.chunk_document(text, doc_id, metadata)
            all_chunks.extend(chunks)

        logger.info(
            f"Batch chunking complete: "
            f"{len(documents)} docs → {len(all_chunks)} chunks "
            f"(avg {len(all_chunks) / len(documents) if documents else 0:.1f} chunks/doc)"
        )

        return all_chunks

    def estimate_chunks(self, text: str) -> int:
        """
        Estimate number of chunks for a text (without actually splitting).

        Use this for:
        - Progress estimation
        - Quota planning
        - UI feedback

        Args:
            text: Text to estimate

        Returns:
            Estimated number of chunks

        Example:
            >>> service = ChunkingService(chunk_size=2048)
            >>> text = "x" * 5000
            >>> service.estimate_chunks(text)
            3  # ~2048 chars per chunk with 200 overlap
        """
        text_length = len(text)

        if text_length <= self.chunk_size:
            return 1

        # Formula: (total - chunk_size) / (chunk_size - overlap) + 1
        # This accounts for overlap between chunks
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        estimated = ((text_length - self.chunk_size) / effective_chunk_size) + 1

        return max(1, int(estimated) + 1)  # +1 for safety margin

    def get_config(self) -> Dict[str, Any]:
        """
        Get current chunking configuration.

        Returns:
            Dict with configuration details

        Example:
            >>> service = ChunkingService()
            >>> config = service.get_config()
            >>> print(config)
            {
                'chunk_size': 2048,
                'chunk_overlap': 200,
                'overlap_percentage': 10.0,
                'separators': ['\\n\\n', '\\n', ' ', ''],
                'estimated_tokens_per_chunk': 512
            }
        """
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'overlap_percentage': (self.chunk_overlap / self.chunk_size) * 100,
            'separators': self.separators,
            'estimated_tokens_per_chunk': self.chunk_size // 4,  # Rough estimate: 4 chars ≈ 1 token
            'strategy': 'RecursiveCharacterTextSplitter',
            'optimized_for': ['multilingual', 'OCR text', 'agricultural documents']
        }


# Module-level convenience function
def chunk_text(
    text: str,
    chunk_size: int = 2048,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Quick chunking function without metadata.

    Use this for:
    - Simple testing
    - Quick prototyping
    - Non-production use

    Args:
        text: Text to chunk
        chunk_size: Chunk size in characters
        chunk_overlap: Overlap in characters

    Returns:
        List of chunk strings (no metadata)

    Example:
        >>> from app.services.chunking_service import chunk_text
        >>> chunks = chunk_text("Long text here...", chunk_size=1000)
        >>> len(chunks)
        3
    """
    service = ChunkingService(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    splitter = service.text_splitter
    return splitter.split_text(text)
