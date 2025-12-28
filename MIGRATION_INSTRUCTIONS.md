# Instructions Migration Supabase - Context Documents

## 📋 À FAIRE MAINTENANT

### Étape 1: Ouvrir Supabase Dashboard

1. Va sur: **https://supabase.com/dashboard**
2. Sélectionne ton projet: **Cambodia Agri Analytics**
3. Dans le menu gauche, clique sur: **SQL Editor**

### Étape 2: Copier/Coller ce SQL

**COPIE TOUT LE SQL CI-DESSOUS** et colle-le dans l'éditeur SQL:

```sql
-- Create context_documents table for storing PDF and document extracts
-- These documents provide crucial contextual information for agricultural analysis

CREATE TABLE IF NOT EXISTS public.context_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type TEXT NOT NULL DEFAULT 'context',
    source TEXT NOT NULL,
    commodity TEXT,
    title TEXT NOT NULL,
    text_content TEXT NOT NULL,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    char_count INTEGER,
    extraction_method TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_context_documents_source ON public.context_documents(source);
CREATE INDEX IF NOT EXISTS idx_context_documents_commodity ON public.context_documents(commodity);
CREATE INDEX IF NOT EXISTS idx_context_documents_scraped_at ON public.context_documents(scraped_at DESC);

-- Enable Row Level Security
ALTER TABLE public.context_documents ENABLE ROW LEVEL SECURITY;

-- Create policy for read access (public read)
CREATE POLICY "Allow public read access on context_documents"
    ON public.context_documents
    FOR SELECT
    USING (true);

-- Create policy for insert access (authenticated users)
CREATE POLICY "Allow authenticated insert on context_documents"
    ON public.context_documents
    FOR INSERT
    WITH CHECK (true);

-- Create policy for update access (authenticated users) - IMPORTANT for upserts!
CREATE POLICY "Allow authenticated update on context_documents"
    ON public.context_documents
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_context_documents_updated_at
    BEFORE UPDATE ON public.context_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment
COMMENT ON TABLE public.context_documents IS 'Stores extracted text from PDFs and documents for contextual analysis. These documents provide crucial background information about agricultural policies, concessions, market reports, and industry context even when they do not contain structured production data.';
```

### Étape 3: Exécuter

1. Clique sur le bouton **"RUN"** (ou appuie sur Ctrl+Enter)
2. Attends le message de succès ✅

### Étape 4: Vérifier

Tu devrais voir:
- ✅ Table created successfully
- ✅ 3 indexes created
- ✅ 3 policies created
- ✅ 1 trigger created

## 🧪 APRÈS la migration, teste avec:

```bash
python scripts/test_context_documents.py
```

Tu devrais voir:
- ✅ Table exists!
- ✅ Inserted document
- ✅ Updated document
- ✅ Found X test documents
- ✅ Database statistics

## 🚀 ENSUITE, lance la collection complète:

```bash
python scripts/seed_collectors.py --include-odc
```

Ça va collecter:
- **8 PDFs ODC** → context_documents
- **32 PDFs GDrive** → context_documents
- **Total: ~40 documents contextuels** avec ~200,000-320,000 caractères

## 📊 Vérifier les résultats:

Dans Supabase Dashboard → Table Editor → context_documents

Tu verras tous les PDFs avec:
- source (ODC/GDrive)
- commodity (cashew/rubber)
- title (nom du fichier)
- text_content (texte complet extrait)
- char_count (nombre de caractères)
- extraction_method (text/ocr)

---

**C'est tout! Le système captera maintenant TOUS les PDFs comme contexte pour l'analyse finale.** 🎉
