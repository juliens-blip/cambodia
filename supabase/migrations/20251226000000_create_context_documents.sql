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
