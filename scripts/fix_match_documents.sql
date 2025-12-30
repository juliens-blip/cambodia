-- Migration: Corriger match_documents pour 1024 dimensions
-- Le modèle multilingual-e5-small utilise 1024 dimensions, pas 384

-- 1. Supprimer toutes les versions existantes de match_documents
DROP FUNCTION IF EXISTS match_documents(vector, integer, double precision, text);
DROP FUNCTION IF EXISTS match_documents(vector(384), integer, double precision, text);
DROP FUNCTION IF EXISTS match_documents(vector(1024), integer, double precision, text);

-- 2. Recréer la fonction avec 1024 dimensions (multilingual-e5-small)
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1024),
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
        de.id,
        de.document_id,
        de.chunk_index,
        de.chunk_text,
        1 - (de.embedding <=> query_embedding) AS similarity,
        de.metadata
    FROM document_embeddings de
    WHERE
        -- Filter by similarity threshold
        1 - (de.embedding <=> query_embedding) >= match_threshold
        -- Filter by commodity if specified
        AND (
            filter_commodity IS NULL
            OR de.metadata->>'commodity' = filter_commodity
        )
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 3. Ajouter commentaire
COMMENT ON FUNCTION match_documents IS 'Recherche sémantique avec multilingual-e5-small (1024 dimensions)';

-- 4. Vérifier que la table document_embeddings existe et a la bonne structure
DO $$
BEGIN
    -- Vérifier si document_embeddings existe
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'document_embeddings'
    ) THEN
        RAISE NOTICE '✅ Table document_embeddings existe';
    ELSE
        RAISE EXCEPTION '❌ Table document_embeddings n''existe pas - migration requise';
    END IF;

    RAISE NOTICE '✅ Fonction match_documents mise à jour (1024 dimensions)';
    RAISE NOTICE 'Prochaine étape: indexer les 34 documents Google Drive';
END $$;
