description: FIX - Corriger l'upload d'images vers le champ Attachments Airtable
allowed-tools: [Read, Write, Edit, Bash]
argument-hint: none
model: sonnet

# IMAGE FIX COMMAND - ResidConnect SaaS

## Problème identifié
Les images n'apparaissent pas dans Airtable, mais les autres champs (titre, description) fonctionnent.
Cela signifie que le format JSON envoyé à Airtable est mauvais pour le champ Attachments.

## Diagnostic de Gemini
1. Token API ✅ OK
2. Base ID + Table ID ✅ OK  
3. Connexion Airtable ✅ OK
4. ❌ PROBLÈME: Format du champ Attachments dans le JSON

---

# PHASE 1: DIAGNOSTIQUE

## Step 1: Vérifier les 3 points critiques

### Point 1: Format JSON
Read(app/api/tenant/tickets/route.ts)
  → Chercher la partie où on construit `fields`
  → Afficher comment images_urls est ajouté

### Point 2: Nom exact du champ
Read(app/api/tenant/tickets/route.ts)
  → Chercher le nom du champ utilisé (images_urls, Images, Attachments, etc.)

Read(claude.md)
  → Chercher la section AIRTABLE SCHEMA REFERENCE
  → Vérifier le nom EXACT du champ pour TICKETS
  → Afficher le Field ID et le nom

### Point 3: Test debug
Read(components/TicketForm.tsx)
  → Vérifier comment uploadedImage est envoyé au backend
  → Vérifier la fonction handleSubmit

---

# PHASE 2: PLAN DE CORRECTION

## 3 corrections à appliquer

### Correction 1: Format JSON strict
Dans app/api/tenant/tickets/route.ts:

Avant (❌ N'AIME PAS AIRTABLE):
```typescript
fields["images_urls"] = body.images_urls; // Envoi direct (MAUVAIS)
```

Après (✅ AIRTABLE AIME):
```typescript
if (body.images_urls && Array.isArray(body.images_urls) && body.images_urls.length > 0) {
  // STRICT: Airtable veut un tableau d'objets avec JUSTE l'ID
  fields["images_urls"] = body.images_urls.map((img: any) => ({
    id: img.id  // ← OBLIGATOIRE, c'est LA clé qu'Airtable cherche
  }));
}
```

### Correction 2: Vérifier le nom du champ
Airtable est sensible à la casse:
- "images_urls" ≠ "Images_urls" ≠ "Images" ≠ "Attachments"

Vérifier dans CLAUDE.md:
- TICKETS table
- Chercher le champ avec type Attachments
- Copier le NOM EXACT (case-sensitive)

### Correction 3: Ajouter les console.log de debug
Dans app/api/tenant/tickets/route.ts, AVANT le fetch Airtable:

```typescript
console.log("🔍 DEBUG IMAGE - Body reçu du frontend:", body.images_urls);
console.log("🔍 DEBUG IMAGE - ID extrait:", body.images_urls?.[0]?.id);
console.log("🔍 DEBUG IMAGE - Payload envoyé à Airtable:", JSON.stringify(fields, null, 2));
```

Ça affichera dans le terminal npm run dev.

---

# PHASE 3: IMPLÉMENTATION

## Step 3A: Corriger app/api/tenant/tickets/route.ts

Edit(app/api/tenant/tickets/route.ts)
  
  → Chercher la partie POST qui crée le ticket
  
  → Chercher où on ajoute images_urls aux fields
  
  → Remplacer par:
```typescript
// === GESTION DES IMAGES - FORMAT STRICT AIRTABLE ===
if (body.images_urls && Array.isArray(body.images_urls) && body.images_urls.length > 0) {
  // Airtable est TRÈS strict: il faut un tableau d'objets {id: "attXXXX"}
  // Ne pas envoyer l'objet complet, juste l'ID !
  fields["images_urls"] = body.images_urls.map((img: any) => ({
    id: img.id  // ← CLEF ABSOLUE: c'est ce que Airtable attend
  }));
  
  console.log("✅ Images_urls format Airtable:", JSON.stringify(fields["images_urls"], null, 2));
}
```

  → Ajouter les console.log AVANT le fetch Airtable:
```typescript
console.log("🔍 DEBUG - Body reçu:", body.images_urls);
console.log("🔍 DEBUG - ID extrait:", body.images_urls?.[0]?.id);
console.log("🔍 DEBUG - Payload complet à Airtable:", JSON.stringify(fields, null, 2));
```

  → Vérifier que le nom du champ est EXACTEMENT celui d'Airtable
    (chercher dans CLAUDE.md le nom exact du champ Attachments)

## Step 3B: Vérifier que TicketForm envoie les bonnes données

Read(components/TicketForm.tsx)
  → Chercher la fonction handleSubmit
  → Vérifier que uploadedImage est passé à l'API

Edit(components/TicketForm.tsx)
  → Si uploadedImage existe, ajouter au body:
```typescript
const body = {
  title,
  description,
  category,
  priority,
  // ... autres champs
  images_urls: uploadedImage ? [uploadedImage] : [] // ← S'ASSURER QUE C'EST UN TABLEAU
};
```

---

# PHASE 4: TEST

## Step 4: Tester la correction

Bash(npm run dev)
  → Redémarrer le serveur

Test Flow:
1. Aller à /tenant/tickets/new
2. Uploader une image
3. Remplir le formulaire (titre, description, etc.)
4. Soumettre le formulaire
5. REGARDER LE TERMINAL npm run dev
   → Chercher les logs 🔍 DEBUG
   → Vérifier que vous voyez un ID type "attXXXXXXXX"

Résultats attendus:

**Cas A: ❌ Vous voyez "undefined"**
  → Problème: uploadedImage n'est pas envoyé du frontend
  → Solution: Vérifier handleSubmit dans TicketForm.tsx

**Cas B: ✅ Vous voyez "attXXXXXXXX"**
  → Upload a marché !
  → Vérifier Airtable pour voir si l'image apparaît
  → Si encore vide: c'est le formatage JSON (correction 1)

**Cas C: ❌ Vous voyez le payload complet MAIS image vide dans Airtable**
  → Problème: Format JSON incorrect ou nom du champ mauvais
  → Solutions:
    1. Vérifier que fields["images_urls"] est un tableau d'objets avec {id}
    2. Vérifier le nom du champ (exactement comme dans Airtable)

---

# PHASE 5: SI ÇA NE MARCHE TOUJOURS PAS

Si après ces corrections ça ne marche pas:

**Option A: Utiliser des URLs au lieu d'IDs**
```typescript
fields["images_urls"] = body.images_urls.map((img: any) => ({
  url: img.url // Au lieu de id
}));
```

**Option B: Basculer sur Cloudinary**
```
Airtable bloque peut-être l'API uploadAttachment
Solution: Uploader vers Cloudinary au lieu de Airtable
Frontend: Envoyer URL Cloudinary au lieu d'ID Airtable
Backend: Stocker l'URL dans un champ Text au lieu d'Attachments
```

---

# PHASE 6: RÉSUMÉ

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ IMAGE UPLOAD FIX APPLIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✏️ CORRECTIONS APPLIQUÉES:

1. ✅ Format JSON strict pour Attachments
   → fields["images_urls"] = [{id: "attXXX"}]
   
2. ✅ Nom du champ vérifié
   → "images_urls" (case-sensitive)
   
3. ✅ Console.log ajoutés pour debug
   → Affiche l'ID reçu du frontend
   → Affiche le payload envoyé à Airtable

📊 TESTS:

Terminal:
  npm run dev
  → Regarder les logs 🔍 DEBUG IMAGE

Browser:
  → Uploader une image
  → Créer un ticket
  → Vérifier Airtable (image doit apparaître)

📝 SI ERREUR:
  → Vérifier les logs du terminal
  → Cas A (undefined): frontend n'envoie pas uploadedImage
  → Cas B (attXXXX ok): image vide = formatage JSON
  → Cas C (tout bon): Airtable bloque → utiliser Cloudinary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# UTILISATION
