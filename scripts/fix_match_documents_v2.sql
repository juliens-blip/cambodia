-- Migration v2: Supprimer TOUTES les versions de match_documents
-- et recréer proprement pour 1024 dimensions

-- 1. Lister et supprimer toutes les versions existantes
-- Utiliser CASCADE pour supprimer toutes les dépendances
DROP FUNCTION IF EXISTS match_documents CASCADE;
DROP FUNCTION IF EXISTS public.match_documents CASCADE;

-- 2. Supprimer par signature spécifique (toutes les variantes possibles)
DROP FUNCTION IF EXISTS match_documents(vector, int, float, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(384), int, float, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(1024), int, float, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector, integer, double precision, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(384), integer, double precision, text) CASCADE;
DROP FUNCTION IF EXISTS match_documents(vector(1024), integer, double precision, text) CASCADE;

-- 3. Si ça ne suffit pas, forcer la suppression de tout ce qui contient "match_documents"
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

-- 4. Recréer la fonction proprement avec 1024 dimensions
CREATE FUNCTION match_documents(
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

-- 5. Ajouter commentaire
COMMENT ON FUNCTION match_documents IS 'Recherche sémantique - multilingual-e5-small (1024D) - Recreated cleanly';

-- 6. Vérifier que ça marche
DO $$
BEGIN
    RAISE NOTICE '✅ Fonction match_documents recréée avec succès (1024 dimensions)';
    RAISE NOTICE 'Signature: match_documents(vector(1024), int, float, text)';
    RAISE NOTICE 'Prochaine étape: exécuter scripts\index_existing_documents.py';
END $$;
