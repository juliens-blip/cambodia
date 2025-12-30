-- Migration: Corriger match_documents pour 384 dimensions
-- Le modèle multilingual-e5-small utilise 384 dimensions, pas 1024

-- 1. Supprimer toutes les versions existantes
DROP FUNCTION IF EXISTS match_documents CASCADE;
DROP FUNCTION IF EXISTS public.match_documents CASCADE;

-- 2. Supprimer par signature spécifique
DROP FUNCTION IF EXISTS match_documents(vector, int, float, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(384), int, float, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(1024), int, float, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector, integer, double precision, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(384), integer, double precision, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(1024), integer, double precision, text) CASCADE;

-- 3. Forcer suppression dynamique
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT
            'DROP FUNCTION IF EXISTS ' || ns.nspname || '.' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ') CASCADE;' AS drop_cmd
        FROM pg_proc p
        JOIN pg_namespace ns ON p.pronamespace = ns.oid
        WHERE p.proname = 'match_documents'
          AND ns.nspname = 'public'
    LOOP
        EXECUTE r.drop_cmd;
        RAISE NOTICE 'Dropped: %', r.drop_cmd;
    END LOOP;
END $$;

-- 4. Recréer avec 384 dimensions (multilingual-e5-small)
CREATE FUNCTION match_documents(
    query_embedding vector(384),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.5,
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
        1 - (de.embedding <=> query_embedding) >= match_threshold
        AND (
            filter_commodity IS NULL
            OR de.metadata->>'commodity' = filter_commodity
        )
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 5. Vérifier la colonne embedding dans document_embeddings
-- Si elle existe avec 1024D, la modifier pour 384D
DO $$
BEGIN
    -- Vérifier si la table existe
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'document_embeddings') THEN
        -- Modifier la colonne si nécessaire (attention: supprime les données existantes)
        ALTER TABLE document_embeddings
        ALTER COLUMN embedding TYPE vector(384);
        RAISE NOTICE '✅ Colonne embedding modifiée pour 384 dimensions';
    END IF;
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Note: %', SQLERRM;
END $$;

-- 6. Commentaire
COMMENT ON FUNCTION match_documents IS 'Recherche sémantique - multilingual-e5-small (384D)';

-- 7. Confirmation
DO $$
BEGIN
    RAISE NOTICE '✅ Fonction match_documents recréée (384 dimensions)';
    RAISE NOTICE 'Prochaine étape: lancer indexation via page Admin';
END $$;
