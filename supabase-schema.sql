-- ============================================================
-- SCHEMA SUPABASE POUR RESIDCONNECT
-- Migration depuis Airtable vers Supabase PostgreSQL
-- ============================================================

-- Activer l'extension UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLES
-- ============================================================

-- TABLE: tenants (locataires)
CREATE TABLE IF NOT EXISTS tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_user_id UUID UNIQUE,
  email TEXT UNIQUE NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  unit TEXT,
  phone TEXT,
  residence_name TEXT DEFAULT 'ResidConnect',
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE: professionals (professionnels)
CREATE TABLE IF NOT EXISTS professionals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_user_id UUID UNIQUE,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('plumber', 'electrician', 'concierge', 'agency')),
  phone TEXT,
  agency_email TEXT,
  specialties TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE: residences
CREATE TABLE IF NOT EXISTS residences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  address TEXT NOT NULL,
  agency_email TEXT NOT NULL,
  total_units INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE: tickets
CREATE TABLE IF NOT EXISTS tickets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('plomberie', 'électricité', 'concierge', 'autre')),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'assigned', 'in_progress', 'resolved', 'closed')),
  priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),

  -- Foreign keys
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  tenant_email TEXT NOT NULL,
  professional_id UUID REFERENCES professionals(id) ON DELETE SET NULL,
  residence_id UUID REFERENCES residences(id) ON DELETE SET NULL,

  unit TEXT,

  -- Stockage Supabase Storage (array d'URLs)
  images_urls TEXT[],
  invoice_url TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  resolution_notes TEXT
);

-- TABLE: messages
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  titre TEXT NOT NULL,
  message TEXT NOT NULL,
  categorie TEXT NOT NULL CHECK (categorie IN ('intervention', 'evenement', 'general')),

  -- Foreign keys (one or the other)
  tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
  professional_id UUID REFERENCES professionals(id) ON DELETE SET NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES POUR PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email);
CREATE INDEX IF NOT EXISTS idx_tenants_auth_user_id ON tenants(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);

CREATE INDEX IF NOT EXISTS idx_professionals_email ON professionals(email);
CREATE INDEX IF NOT EXISTS idx_professionals_auth_user_id ON professionals(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_professionals_type ON professionals(type);

CREATE INDEX IF NOT EXISTS idx_residences_name ON residences(name);

CREATE INDEX IF NOT EXISTS idx_tickets_tenant_id ON tickets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tickets_tenant_email ON tickets(tenant_email);
CREATE INDEX IF NOT EXISTS idx_tickets_professional_id ON tickets(professional_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_categorie ON messages(categorie);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_tenant_id ON messages(tenant_id);
CREATE INDEX IF NOT EXISTS idx_messages_professional_id ON messages(professional_id);

-- ============================================================
-- TRIGGERS: Auto-update updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
CREATE TRIGGER update_tenants_updated_at
  BEFORE UPDATE ON tenants
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_professionals_updated_at ON professionals;
CREATE TRIGGER update_professionals_updated_at
  BEFORE UPDATE ON professionals
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_residences_updated_at ON residences;
CREATE TRIGGER update_residences_updated_at
  BEFORE UPDATE ON residences
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tickets_updated_at ON tickets;
CREATE TRIGGER update_tickets_updated_at
  BEFORE UPDATE ON tickets
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- TRIGGER: Auto-assignation professionnel aux tickets
-- ============================================================

CREATE OR REPLACE FUNCTION assign_professional_to_ticket()
RETURNS TRIGGER AS $$
DECLARE
  prof_id UUID;
BEGIN
  -- Si un professionnel est déjà assigné, ne rien faire
  IF NEW.professional_id IS NOT NULL THEN
    RETURN NEW;
  END IF;

  -- Mapper la catégorie vers le type de professionnel
  SELECT id INTO prof_id
  FROM professionals
  WHERE type = CASE NEW.category
    WHEN 'plomberie' THEN 'plumber'
    WHEN 'électricité' THEN 'electrician'
    WHEN 'concierge' THEN 'concierge'
    WHEN 'autre' THEN 'agency'
    ELSE NULL
  END
  LIMIT 1;

  -- Assigner le professionnel si trouvé
  IF prof_id IS NOT NULL THEN
    NEW.professional_id := prof_id;
    NEW.status := 'assigned';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS auto_assign_professional ON tickets;
CREATE TRIGGER auto_assign_professional
  BEFORE INSERT ON tickets
  FOR EACH ROW
  EXECUTE FUNCTION assign_professional_to_ticket();

-- ============================================================
-- TRIGGER: Sync auth.users avec tables tenants/professionals
-- ============================================================

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  -- Créer/mettre à jour un tenant si role = 'tenant' (idempotent)
  IF NEW.raw_user_meta_data->>'role' = 'tenant' THEN
    INSERT INTO tenants (
      auth_user_id,
      email,
      first_name,
      last_name,
      unit,
      phone,
      residence_name,
      status
    ) VALUES (
      NEW.id,
      NEW.email,
      COALESCE(NEW.raw_user_meta_data->>'first_name', ''),
      COALESCE(NEW.raw_user_meta_data->>'last_name', ''),
      NEW.raw_user_meta_data->>'unit',
      NEW.raw_user_meta_data->>'phone',
      COALESCE(NEW.raw_user_meta_data->>'residence_name', 'ResidConnect'),
      'active'
    )
    ON CONFLICT (email) DO UPDATE
      SET auth_user_id   = EXCLUDED.auth_user_id,
          first_name     = COALESCE(EXCLUDED.first_name, tenants.first_name),
          last_name      = COALESCE(EXCLUDED.last_name, tenants.last_name),
          unit           = COALESCE(EXCLUDED.unit, tenants.unit),
          phone          = COALESCE(EXCLUDED.phone, tenants.phone),
          residence_name = COALESCE(EXCLUDED.residence_name, tenants.residence_name),
          status         = 'active',
          updated_at     = NOW();

  -- Créer/mettre à jour un professional si role = 'professional' (idempotent)
  ELSIF NEW.raw_user_meta_data->>'role' = 'professional' THEN
    INSERT INTO professionals (
      auth_user_id,
      email,
      name,
      type,
      phone,
      agency_email,
      specialties
    ) VALUES (
      NEW.id,
      NEW.email,
      COALESCE(NEW.raw_user_meta_data->>'name', ''),
      COALESCE(NEW.raw_user_meta_data->>'type', 'agency'),
      NEW.raw_user_meta_data->>'phone',
      NEW.raw_user_meta_data->>'agency_email',
      NEW.raw_user_meta_data->>'specialties'
    )
    ON CONFLICT (email) DO UPDATE
      SET auth_user_id = EXCLUDED.auth_user_id,
          name         = COALESCE(EXCLUDED.name, professionals.name),
          type         = COALESCE(EXCLUDED.type, professionals.type),
          phone        = COALESCE(EXCLUDED.phone, professionals.phone),
          agency_email = COALESCE(EXCLUDED.agency_email, professionals.agency_email),
          specialties  = COALESCE(EXCLUDED.specialties, professionals.specialties),
          updated_at   = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Activer RLS sur toutes les tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE professionals ENABLE ROW LEVEL SECURITY;
ALTER TABLE residences ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- RLS POLICIES: TENANTS
-- ============================================================

DROP POLICY IF EXISTS "Tenants can view own data" ON tenants;
CREATE POLICY "Tenants can view own data"
  ON tenants FOR SELECT
  USING (auth_user_id = auth.uid());

DROP POLICY IF EXISTS "Tenants can update own data" ON tenants;
CREATE POLICY "Tenants can update own data"
  ON tenants FOR UPDATE
  USING (auth_user_id = auth.uid());

DROP POLICY IF EXISTS "Professionals can view all tenants" ON tenants;
CREATE POLICY "Professionals can view all tenants"
  ON tenants FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM professionals
      WHERE auth_user_id = auth.uid()
    )
  );

-- ============================================================
-- RLS POLICIES: PROFESSIONALS
-- ============================================================

DROP POLICY IF EXISTS "Professionals can view own data" ON professionals;
CREATE POLICY "Professionals can view own data"
  ON professionals FOR SELECT
  USING (auth_user_id = auth.uid());

DROP POLICY IF EXISTS "Professionals can update own data" ON professionals;
CREATE POLICY "Professionals can update own data"
  ON professionals FOR UPDATE
  USING (auth_user_id = auth.uid());

DROP POLICY IF EXISTS "Tenants can view all professionals" ON professionals;
CREATE POLICY "Tenants can view all professionals"
  ON professionals FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM tenants
      WHERE auth_user_id = auth.uid()
    )
  );

-- ============================================================
-- RLS POLICIES: TICKETS
-- ============================================================

DROP POLICY IF EXISTS "Tenants can view own tickets" ON tickets;
CREATE POLICY "Tenants can view own tickets"
  ON tickets FOR SELECT
  USING (
    tenant_id IN (
      SELECT id FROM tenants WHERE auth_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Tenants can create tickets" ON tickets;
CREATE POLICY "Tenants can create tickets"
  ON tickets FOR INSERT
  WITH CHECK (
    tenant_id IN (
      SELECT id FROM tenants WHERE auth_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Professionals can view assigned tickets" ON tickets;
CREATE POLICY "Professionals can view assigned tickets"
  ON tickets FOR SELECT
  USING (
    professional_id IN (
      SELECT id FROM professionals WHERE auth_user_id = auth.uid()
    )
    OR
    EXISTS (
      SELECT 1 FROM professionals
      WHERE auth_user_id = auth.uid() AND type = 'agency'
    )
  );

DROP POLICY IF EXISTS "Professionals can update tickets" ON tickets;
CREATE POLICY "Professionals can update tickets"
  ON tickets FOR UPDATE
  USING (
    professional_id IN (
      SELECT id FROM professionals WHERE auth_user_id = auth.uid()
    )
    OR
    EXISTS (
      SELECT 1 FROM professionals
      WHERE auth_user_id = auth.uid() AND type = 'agency'
    )
  );

-- ============================================================
-- RLS POLICIES: MESSAGES
-- ============================================================

DROP POLICY IF EXISTS "Authenticated users can view messages" ON messages;
CREATE POLICY "Authenticated users can view messages"
  ON messages FOR SELECT
  USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Tenants can create messages" ON messages;
CREATE POLICY "Tenants can create messages"
  ON messages FOR INSERT
  WITH CHECK (
    tenant_id IN (
      SELECT id FROM tenants WHERE auth_user_id = auth.uid()
    )
    AND professional_id IS NULL
  );

DROP POLICY IF EXISTS "Professionals can create messages" ON messages;
CREATE POLICY "Professionals can create messages"
  ON messages FOR INSERT
  WITH CHECK (
    professional_id IN (
      SELECT id FROM professionals WHERE auth_user_id = auth.uid()
    )
    AND tenant_id IS NULL
  );

-- ============================================================
-- RLS POLICIES: RESIDENCES
-- ============================================================

DROP POLICY IF EXISTS "Authenticated users can view residences" ON residences;
CREATE POLICY "Authenticated users can view residences"
  ON residences FOR SELECT
  USING (auth.role() = 'authenticated');

-- ============================================================
-- STORAGE: Buckets et RLS
-- ============================================================

-- Créer les buckets (si pas déjà créés via UI)
INSERT INTO storage.buckets (id, name, public)
VALUES ('ticket-images', 'ticket-images', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('invoices', 'invoices', false)
ON CONFLICT (id) DO NOTHING;

-- RLS pour storage: ticket-images
DROP POLICY IF EXISTS "Upload ticket images" ON storage.objects;
CREATE POLICY "Upload ticket images"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'ticket-images'
    AND auth.role() = 'authenticated'
  );

DROP POLICY IF EXISTS "View ticket images" ON storage.objects;
CREATE POLICY "View ticket images"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'ticket-images');

DROP POLICY IF EXISTS "Delete ticket images" ON storage.objects;
CREATE POLICY "Delete ticket images"
  ON storage.objects FOR DELETE
  USING (
    bucket_id = 'ticket-images'
    AND (
      -- Tenant qui a créé le ticket
      EXISTS (
        SELECT 1 FROM tickets t
        JOIN tenants tn ON t.tenant_id = tn.id
        WHERE t.id::text = split_part(storage.objects.name, '/', 1)
        AND tn.auth_user_id = auth.uid()
      )
      OR
      -- Professionnel assigné au ticket
      EXISTS (
        SELECT 1 FROM tickets t
        JOIN professionals p ON t.professional_id = p.id
        WHERE t.id::text = split_part(storage.objects.name, '/', 1)
        AND p.auth_user_id = auth.uid()
      )
    )
  );

-- RLS pour storage: invoices
DROP POLICY IF EXISTS "Upload invoices" ON storage.objects;
CREATE POLICY "Upload invoices"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'invoices'
    AND EXISTS (
      SELECT 1 FROM professionals WHERE auth_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Tenants view own invoices" ON storage.objects;
CREATE POLICY "Tenants view own invoices"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'invoices'
    AND EXISTS (
      SELECT 1 FROM tickets t
      JOIN tenants tn ON t.tenant_id = tn.id
      WHERE t.id::text = split_part(storage.objects.name, '/', 1)
      AND tn.auth_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Professionals view invoices" ON storage.objects;
CREATE POLICY "Professionals view invoices"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'invoices'
    AND EXISTS (
      SELECT 1 FROM professionals WHERE auth_user_id = auth.uid()
    )
  );

-- ============================================================
-- FIN DU SCHEMA
-- ============================================================

-- Note: Après l'exécution de ce script, vous devrez:
-- 1. Aller dans Authentication > Settings et désactiver "Enable email confirmations" pour dev
-- 2. Créer les buckets Storage manuellement via l'UI si les inserts ci-dessus échouent
-- 3. Mettre à jour vos variables d'environnement dans .env.local
