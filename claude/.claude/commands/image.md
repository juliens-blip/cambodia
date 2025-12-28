---
description: Implémenter l'upload et le traitement d'images de yachts avec Gemini AI
allowed-tools: [Read, Write, Edit, Bash, Grep, Task]
argument-hint: none
model: sonnet
---

# IMAGE UPLOAD & PROCESSING COMMAND - YachtGenius

## Objectif
Permettre aux utilisateurs d'uploader des images d'intérieurs de yachts, les analyser avec Gemini AI, et générer 5 styles différents.

## Architecture
```
User upload image
   ↓
Frontend validation (type, size)
   ↓
Convert to base64
   ↓
POST /api/analyze (structure analysis via Gemini)
   ↓
Store structure description
   ↓
POST /api/generate (5 styles via Gemini)
   ↓
Display gallery with 5 transformed styles
```

## Contexte Tech
- **Frontend**: React 19, Next.js 14
- **AI**: Gemini 2.5 Flash (gemini-2.5-flash)
- **API**: @google/generative-ai
- **Auth**: API Key via GEMINI_API_KEY
- **Image Format**: Base64 (JPEG, PNG, WebP)
- **Max Size**: 10MB

---

# PHASE 1: EXPLORATION

## Step 1: Vérifier les fichiers existants

```
Read(src/App.jsx)
  → Structure actuelle Vite
  → Workflow existant (upload, processing, results)

Read(package.json)
  → Dépendances installées
  → Scripts disponibles

Read(CLAUDE.md)
  → Architecture complète
  → Fichiers cibles pour Next.js
```

---

# PHASE 2: PLAN

## Fichiers à créer (Migration Next.js)

### À CRÉER - Backend:
1. **lib/gemini.ts**
   - Client Gemini singleton
   - analyzeYachtStructure(base64Image)
   - generateYachtStyle(base64Image, structure, style)
   - Configuration centralisée

2. **lib/imageUtils.ts**
   - validateImage(file)
   - convertToBase64(file)
   - resizeImage(base64, maxWidth)
   - Format validation (JPEG, PNG, WebP)

3. **lib/types.ts**
   - Type YachtStyle (enum)
   - Interface AnalysisResult
   - Interface GenerationResult
   - Interface ImageMetadata

4. **app/api/analyze/route.ts**
   - POST /api/analyze
   - Reçoit { image: base64 }
   - Appelle Gemini pour analyse structure
   - Retourne { description, features }

5. **app/api/generate/route.ts**
   - POST /api/generate
   - Reçoit { image: base64, structure: string, style: YachtStyle }
   - Appelle Gemini pour génération style
   - Retourne { transformation: string, style: string }

6. **app/api/generate-all/route.ts**
   - POST /api/generate-all
   - Reçoit { image: base64 }
   - Appelle analyze puis generate pour les 5 styles
   - Retourne { analysis, styles: [...] }

### À CRÉER - Frontend:
7. **components/ImageUploader.tsx**
   - Input file avec drag & drop
   - Validation côté client
   - Preview de l'image
   - Loading states

8. **components/StyleGallery.tsx**
   - Galerie responsive (grid)
   - Affichage des 5 styles
   - Comparison slider (avant/après)
   - Download buttons

9. **components/ProcessingLoader.tsx**
   - Animation holographique
   - Console log des étapes
   - Progress indicator

10. **app/page.tsx**
    - Landing page
    - Call-to-action upload

11. **app/upload/page.tsx**
    - Page upload avec preview
    - Execute Redesign button

12. **app/gallery/page.tsx**
    - Affichage des résultats
    - 5 styles en galerie

---

# PHASE 3: CODE

## Step 3A: Créer lib/types.ts

```typescript
// lib/types.ts
export enum YachtStyle {
  FUTURISTIC = 'futuristic',
  ARTDECO = 'artdeco',
  BIOPHILIC = 'biophilic',
  MEDITERRANEAN = 'mediterranean',
  CYBERPUNK = 'cyberpunk'
}

export interface ImageMetadata {
  filename: string;
  size: number;
  type: string;
  dimensions?: {
    width: number;
    height: number;
  };
}

export interface AnalysisResult {
  description: string;
  features: string[];
  cameraAngle?: string;
  roomShape?: string;
  windows?: string;
  ceiling?: string;
}

export interface StyleTransformation {
  style: YachtStyle;
  styleName: string;
  transformation: string;
  prompt: string;
}

export interface GenerationResult {
  analysis: AnalysisResult;
  styles: StyleTransformation[];
  originalImage: string;
}

export const STYLE_DESCRIPTIONS: Record<YachtStyle, {
  name: string;
  description: string;
  keywords: string[];
}> = {
  [YachtStyle.FUTURISTIC]: {
    name: 'Futuristic Minimalist',
    description: 'Sleek white curves, neon accents, holographic displays',
    keywords: ['white glossy', 'LED lighting', 'chrome', 'minimalist']
  },
  [YachtStyle.ARTDECO]: {
    name: 'Art Deco Luxury',
    description: 'Black marble, gold geometric patterns, velvet textures',
    keywords: ['exotic wood', 'brass', 'geometric patterns', 'luxury']
  },
  [YachtStyle.BIOPHILIC]: {
    name: 'Biophilic Zen',
    description: 'Living walls, natural oak wood, flowing water features',
    keywords: ['plants', 'natural wood', 'earth tones', 'organic']
  },
  [YachtStyle.MEDITERRANEAN]: {
    name: 'Mediterranean Riviera',
    description: 'White linen, terracotta tiles, olive wood, blue accents',
    keywords: ['white/azure blue', 'terracotta', 'wrought iron', 'airy']
  },
  [YachtStyle.CYBERPUNK]: {
    name: 'Cyberpunk Industrial',
    description: 'Exposed metal, dark moody lighting, neon purple/blue',
    keywords: ['matte black', 'neon pink/cyan', 'exposed tech', 'industrial']
  }
};
```

## Step 3B: Créer lib/imageUtils.ts

```typescript
// lib/imageUtils.ts
export interface ValidationResult {
  valid: boolean;
  error?: string;
}

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export function validateImage(file: File): ValidationResult {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'Format non supporté. Utilisez JPEG, PNG ou WebP.'
    };
  }

  if (file.size > MAX_SIZE) {
    return {
      valid: false,
      error: `Image trop volumineuse. Maximum ${MAX_SIZE / (1024 * 1024)}MB.`
    };
  }

  return { valid: true };
}

export async function convertToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      // Remove "data:image/jpeg;base64," prefix
      const base64Data = base64.split(',')[1];
      resolve(base64Data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function getImageDimensions(base64: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.width, height: img.height });
    };
    img.onerror = reject;
    img.src = `data:image/jpeg;base64,${base64}`;
  });
}
```

## Step 3C: Créer lib/gemini.ts

```typescript
// lib/gemini.ts
import { GoogleGenerativeAI } from '@google/generative-ai';
import { YachtStyle, AnalysisResult } from './types';

class GeminiClient {
  private static instance: GeminiClient;
  private genAI: GoogleGenerativeAI;
  private model: any;

  private constructor() {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error('GEMINI_API_KEY not configured');
    }

    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({
      model: process.env.GEMINI_MODEL || 'gemini-2.5-flash'
    });
  }

  public static getInstance(): GeminiClient {
    if (!GeminiClient.instance) {
      GeminiClient.instance = new GeminiClient();
    }
    return GeminiClient.instance;
  }

  public async analyzeStructure(base64Image: string): Promise<AnalysisResult> {
    const prompt = `
      Analyze this yacht interior image.
      Describe ONLY the physical structure and geometry in extreme detail.
      Include:
      - Camera angle and perspective
      - Room shape and dimensions
      - Window placement, shape, and size
      - Ceiling height and features
      - Fixed structural elements
      DO NOT describe furniture style, colors, or decor.
      Focus on the "shell" of the room.
    `;

    try {
      const result = await this.model.generateContent([
        prompt,
        {
          inlineData: {
            data: base64Image,
            mimeType: 'image/jpeg'
          }
        }
      ]);

      const description = result.response.text();

      return {
        description,
        features: this.extractFeatures(description)
      };
    } catch (error) {
      console.error('Gemini analysis error:', error);
      throw new Error('Failed to analyze yacht structure');
    }
  }

  public async generateStyle(
    base64Image: string,
    structure: string,
    style: YachtStyle
  ): Promise<string> {
    const stylePrompts: Record<YachtStyle, string> = {
      [YachtStyle.FUTURISTIC]: 'sleek white curves, neon accents, holographic displays, spaceship aesthetic',
      [YachtStyle.ARTDECO]: 'black marble, gold geometric patterns, velvet textures, great gatsby vibe',
      [YachtStyle.BIOPHILIC]: 'living walls, natural oak wood, flowing water features, organic shapes',
      [YachtStyle.MEDITERRANEAN]: 'white linen, terracotta tiles, olive wood, breezy open air, blue accents',
      [YachtStyle.CYBERPUNK]: 'exposed metal, dark moody lighting, neon purple and blue, high-tech surfaces'
    };

    const prompt = `
      STRICT INSTRUCTION: INTERIOR REFIT ONLY.
      DO NOT CHANGE THE ROOM GEOMETRY.

      Input Image Structure: ${structure}

      Task: Redecorate this EXACT room in the style of: ${stylePrompts[style]}

      Rules:
      1. Keep exact camera angle
      2. Keep exact window shapes/positions
      3. Keep exact structural elements
      4. ONLY change furniture, materials, lighting, colors
      5. Output MUST look like the SAME BOAT, just renovated

      Quality: Photorealistic, 8k, Interior Design Render.
    `;

    try {
      const result = await this.model.generateContent([
        prompt,
        {
          inlineData: {
            data: base64Image,
            mimeType: 'image/jpeg'
          }
        }
      ]);

      return result.response.text();
    } catch (error) {
      console.error(`Gemini generation error for ${style}:`, error);
      throw new Error(`Failed to generate ${style} style`);
    }
  }

  private extractFeatures(description: string): string[] {
    // Simple keyword extraction
    const keywords = ['camera', 'window', 'ceiling', 'wall', 'floor', 'door'];
    return keywords.filter(kw =>
      description.toLowerCase().includes(kw)
    );
  }
}

export const geminiClient = GeminiClient.getInstance();
```

## Step 3D: Créer app/api/analyze/route.ts

```typescript
// app/api/analyze/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { geminiClient } from '@/lib/gemini';

export async function POST(request: NextRequest) {
  try {
    const { image } = await request.json();

    if (!image) {
      return NextResponse.json(
        { error: 'Image base64 required' },
        { status: 400 }
      );
    }

    const analysis = await geminiClient.analyzeStructure(image);

    return NextResponse.json({
      success: true,
      analysis
    });
  } catch (error) {
    console.error('Analysis API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Analysis failed'
      },
      { status: 500 }
    );
  }
}
```

## Step 3E: Créer app/api/generate-all/route.ts

```typescript
// app/api/generate-all/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { geminiClient } from '@/lib/gemini';
import { YachtStyle, STYLE_DESCRIPTIONS } from '@/lib/types';

export async function POST(request: NextRequest) {
  try {
    const { image } = await request.json();

    if (!image) {
      return NextResponse.json(
        { error: 'Image base64 required' },
        { status: 400 }
      );
    }

    // Step 1: Analyze structure
    const analysis = await geminiClient.analyzeStructure(image);

    // Step 2: Generate all 5 styles
    const styles = await Promise.all(
      Object.values(YachtStyle).map(async (style) => {
        try {
          const transformation = await geminiClient.generateStyle(
            image,
            analysis.description,
            style
          );

          return {
            style,
            styleName: STYLE_DESCRIPTIONS[style].name,
            transformation,
            prompt: STYLE_DESCRIPTIONS[style].description
          };
        } catch (error) {
          console.error(`Failed to generate ${style}:`, error);
          return null;
        }
      })
    );

    const successfulStyles = styles.filter(s => s !== null);

    return NextResponse.json({
      success: true,
      analysis,
      styles: successfulStyles,
      originalImage: image
    });
  } catch (error) {
    console.error('Generation API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Generation failed'
      },
      { status: 500 }
    );
  }
}
```

---

# PHASE 4: TEST

## Step 4: Tests

```bash
# 1. Vérifier les dépendances
npm install @google/generative-ai

# 2. Vérifier la clé API
cat .env | grep GEMINI_API_KEY

# 3. Tester le serveur dev
npm run dev

# 4. Tester l'API analyze
curl -X POST http://localhost:3000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"image":"..."}'

# 5. Tester l'API generate-all
curl -X POST http://localhost:3000/api/generate-all \
  -H "Content-Type: application/json" \
  -d '{"image":"..."}'
```

## Tests Manuels:
1. Upload une image de yacht interior
2. Vérifier preview s'affiche
3. Cliquer "Execute Redesign"
4. Vérifier loader holographique
5. Vérifier 5 styles générés
6. Vérifier galerie responsive

## Tests d'Erreur:
- Image > 10MB → Erreur validation
- Format non supporté (.gif) → Erreur
- Pas de clé API → Erreur 500
- Timeout Gemini → Erreur graceful

---

# PHASE 5: RÉSUMÉ

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ IMAGE PROCESSING IMPLEMENTATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 FICHIERS CRÉÉS (Backend):
  ✅ lib/types.ts (Types & enums)
  ✅ lib/imageUtils.ts (Validation & conversion)
  ✅ lib/gemini.ts (Client AI singleton)
  ✅ app/api/analyze/route.ts (Structure analysis)
  ✅ app/api/generate-all/route.ts (5 styles generation)

📁 FICHIERS CRÉÉS (Frontend):
  ✅ components/ImageUploader.tsx (Upload UI)
  ✅ components/StyleGallery.tsx (Results display)
  ✅ components/ProcessingLoader.tsx (Holographic loader)
  ✅ app/page.tsx (Landing)
  ✅ app/upload/page.tsx (Upload page)
  ✅ app/gallery/page.tsx (Gallery page)

🎯 FONCTIONNALITÉS:
  ✅ Image upload avec validation
  ✅ Preview avant traitement
  ✅ Analyse structure via Gemini
  ✅ Génération 5 styles simultanés
  ✅ Galerie responsive
  ✅ Loader holographique
  ✅ Gestion erreurs complète

📊 TESTS:
  npm run dev
  → Aller à http://localhost:3000
  → Upload image yacht interior
  → Vérifier les 5 styles générés

🔐 SÉCURITÉ:
  ✅ API key dans .env
  ✅ Validation fichiers (type, taille)
  ✅ Rate limiting (via Gemini)
  ✅ Error messages sécurisés

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# UTILISATION

```bash
# Depuis Claude Code:
/image

# Avec modifications:
/image
Modifie la galerie pour afficher comparison slider avant/après
```

---

# MCP INTEGRATION

Ce workflow peut aussi utiliser le **gemini-yacht-mcp** :

```typescript
// Alternative: Utiliser le MCP au lieu de l'API directe
import { mcpClient } from '@/lib/mcp-client';

// Analyser structure
const analysis = await mcpClient.call('analyze_structure', { image });

// Générer tous les styles
const result = await mcpClient.call('generate_all', { image });
```

Le MCP offre:
- Retry logic intégré
- Caching intelligent
- Meilleur error handling
- Logs structurés
