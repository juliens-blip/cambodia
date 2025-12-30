-- Migration: Créer document_chunks et match_documents pour la recherche sémantique
-- À exécuter dans Supabase SQL Editor

-- 1. Activer l'extension pgvector si pas déjà fait
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Créer la table document_chunks pour stocker les embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384),  -- multilingual-e5-small = 384 dimensions
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Créer des index pour performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON document_chunks USING gin(metadata);

-- 4. Créer l'index HNSW pour recherche vectorielle rapide
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 5. Créer la fonction RPC match_documents
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(384),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.7,
    filter_commodity TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_index INTEGER,
    chunk_text TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.chunk_text,
        1 - (dc.embedding <=> query_embedding) AS similarity,
        dc.metadata
    FROM document_chunks dc
    WHERE
        -- Filter by similarity threshold
        1 - (dc.embedding <=> query_embedding) >= match_threshold
        -- Filter by commodity if specified
        AND (
            filter_commodity IS NULL
            OR dc.metadata->>'commodity' = filter_commodity
        )
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 6. Ajouter des commentaires pour documentation
COMMENT ON TABLE document_chunks IS 'Chunks de documents avec embeddings vectoriels pour recherche sémantique';
COMMENT ON COLUMN document_chunks.embedding IS 'Vecteur d''embedding (multilingual-e5-small, 384 dimensions)';
COMMENT ON FUNCTION match_documents IS 'Recherche sémantique par similarité cosinus dans les chunks de documents';

-- 7. Afficher un message de succès
DO $$
BEGIN
    RAISE NOTICE 'Migration terminée avec succès!';
    RAISE NOTICE 'Tables créées: document_chunks';
    RAISE NOTICE 'Fonction créée: match_documents';
    RAISE NOTICE 'Prochaine étape: exécuter le script d''indexation Python';
END $$;
