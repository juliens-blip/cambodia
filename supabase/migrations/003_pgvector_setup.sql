-- Migration 003: Setup pgvector for semantic search
-- Date: 2025-12-26
-- Description: Enable pgvector extension, create document_embeddings table with HNSW index

-- ============================================================================
-- STEP 1: Enable pgvector extension
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- STEP 2: Create document_embeddings table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.context_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1024),  -- multilingual-e5-large dimension
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique chunks per document
    CONSTRAINT unique_document_chunk UNIQUE (document_id, chunk_index)
);

-- ============================================================================
-- STEP 3: Create indexes
-- ============================================================================

-- Index on document_id for filtering
CREATE INDEX IF NOT EXISTS idx_embeddings_document_id
    ON public.document_embeddings(document_id);

-- Index on metadata for filtering by source, commodity, etc.
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata
    ON public.document_embeddings USING GIN(metadata);

-- HNSW index for vector similarity search
-- Parameters:
--   m = 16: Number of connections per node (balance between speed and recall)
--   ef_construction = 64: Quality of index construction (higher = better quality)
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
    ON public.document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- STEP 4: Enable Row Level Security
-- ============================================================================

ALTER TABLE public.document_embeddings ENABLE ROW LEVEL SECURITY;

-- Allow public read access (for semantic search)
CREATE POLICY "Allow public read access on document_embeddings"
    ON public.document_embeddings
    FOR SELECT
    USING (true);

-- Allow authenticated insert (for embedding pipeline)
CREATE POLICY "Allow authenticated insert on document_embeddings"
    ON public.document_embeddings
    FOR INSERT
    WITH CHECK (true);

-- Allow authenticated update
CREATE POLICY "Allow authenticated update on document_embeddings"
    ON public.document_embeddings
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Allow authenticated delete
CREATE POLICY "Allow authenticated delete on document_embeddings"
    ON public.document_embeddings
    FOR DELETE
    USING (true);

-- ============================================================================
-- STEP 5: Create trigger for updated_at
-- ============================================================================

-- Reuse existing update_updated_at_column function
CREATE TRIGGER update_document_embeddings_updated_at
    BEFORE UPDATE ON public.document_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STEP 6: Create RPC function for semantic search
-- ============================================================================

CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1024),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    filter_commodity text DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_index INTEGER,
    chunk_text TEXT,
    metadata JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_embeddings.id,
        document_embeddings.document_id,
        document_embeddings.chunk_index,
        document_embeddings.chunk_text,
        document_embeddings.metadata,
        1 - (document_embeddings.embedding <=> query_embedding) AS similarity
    FROM document_embeddings
    WHERE
        -- Similarity threshold filter
        1 - (document_embeddings.embedding <=> query_embedding) > match_threshold
        -- Optional commodity filter
        AND (
            filter_commodity IS NULL
            OR document_embeddings.metadata->>'commodity' = filter_commodity
        )
    ORDER BY document_embeddings.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- STEP 7: Add helpful comments
-- ============================================================================

COMMENT ON TABLE public.document_embeddings IS
'Stores text chunks and their vector embeddings (multilingual-e5-large, 1024 dim) from context documents for semantic search and RAG.';

COMMENT ON COLUMN public.document_embeddings.embedding IS
'Vector embedding (1024 dimensions) generated by multilingual-e5-large model from Hugging Face.';

COMMENT ON COLUMN public.document_embeddings.chunk_text IS
'Text content of the chunk (~2048 chars, 512 tokens with 10% overlap).';

COMMENT ON COLUMN public.document_embeddings.metadata IS
'JSONB metadata including: source, commodity, title, url, chunk_index, total_chunks, char_count.';

COMMENT ON FUNCTION match_documents IS
'Semantic search function using cosine similarity (<=> operator). Returns top K chunks above threshold, optionally filtered by commodity.';

-- ============================================================================
-- STEP 8: Grant permissions
-- ============================================================================

-- Grant SELECT to anon users (for public semantic search)
GRANT SELECT ON public.document_embeddings TO anon;

-- Grant ALL to authenticated users (for embedding pipeline)
GRANT ALL ON public.document_embeddings TO authenticated;

-- Grant usage on RPC function
GRANT EXECUTE ON FUNCTION match_documents TO anon;
GRANT EXECUTE ON FUNCTION match_documents TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify extension
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE 'pgvector extension enabled';
    ELSE
        RAISE EXCEPTION 'pgvector extension not found';
    END IF;
END $$;

-- Verify table
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_embeddings') THEN
        RAISE NOTICE 'document_embeddings table created';
    ELSE
        RAISE EXCEPTION 'document_embeddings table not found';
    END IF;
END $$;

-- Verify HNSW index
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_embeddings_vector'
        AND tablename = 'document_embeddings'
    ) THEN
        RAISE NOTICE 'HNSW index created';
    ELSE
        RAISE WARNING 'HNSW index may not be created yet (check manually)';
    END IF;
END $$;

-- Final success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 003 complete - pgvector ready for semantic search!';
END $$;
