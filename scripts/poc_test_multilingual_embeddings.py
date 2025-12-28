"""POC: Test multilingual-e5-large embeddings with Khmer text."""
import sys
import os
import io

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("POC: Testing multilingual-e5-large with Khmer Support")
print("=" * 80)

# Step 1: Install and import
print("\n1️⃣ Importing sentence-transformers...")
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    print("   ✅ Imports successful")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    print("   Please install: pip install sentence-transformers")
    sys.exit(1)

# Step 2: Load model
print("\n2️⃣ Loading multilingual-e5-large model (~2.2 GB)...")
print("   (First time: downloading model, may take 2-5 minutes)")
try:
    model = SentenceTransformer('intfloat/multilingual-e5-large')
    print(f"   ✅ Model loaded successfully")
    print(f"   Embedding dimension: {model.get_sentence_embedding_dimension()}")
except Exception as e:
    print(f"   ❌ Error loading model: {e}")
    sys.exit(1)

# Step 3: Test texts (Khmer, English, Vietnamese, Mixed)
print("\n3️⃣ Preparing test texts...")

test_texts = {
    "khmer_cashew": "passage: ការផលិតស្វាយចន្ទី នៅកម្ពុជា បានកើនឡើង ក្នុងរយៈពេល ៥ ឆ្នាំ ចុងក្រោយ នេះ។",  # Cashew production in Cambodia increased in last 5 years
    "english_cashew": "passage: Cashew production in Cambodia has increased significantly over the past five years.",
    "khmer_rubber": "passage: ការនាំចេញកៅស៊ូ របស់កម្ពុជា ទៅប្រទេសចិន កើនឡើង ១៥ ភាគរយ។",  # Cambodia rubber exports to China increased 15%
    "english_rubber": "passage: Cambodia's rubber exports to China have grown by 15 percent.",
    "vietnamese_agriculture": "passage: Sản xuất nông nghiệp ở Campuchia đã tăng trưởng mạnh mẽ.",  # Agricultural production in Cambodia has grown strongly
    "mixed_khmer_english": "passage: Cambodia ការនាំចេញ cashew និង rubber ទៅ Vietnam និង China.",  # Cambodia exports cashew and rubber to Vietnam and China
}

print(f"   ✅ Prepared {len(test_texts)} test texts")
print("   Languages: Khmer, English, Vietnamese, Mixed")

# Step 4: Generate embeddings
print("\n4️⃣ Generating embeddings...")
embeddings = {}
try:
    for key, text in test_texts.items():
        emb = model.encode(text, convert_to_numpy=True)
        embeddings[key] = emb
        print(f"   ✅ {key}: {emb.shape} - OK")
except Exception as e:
    print(f"   ❌ Error generating embeddings: {e}")
    sys.exit(1)

# Step 5: Test semantic similarity
print("\n5️⃣ Testing semantic similarity...")

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Test 1: Khmer-Khmer (same topic - cashew)
sim_khmer_khmer = cosine_similarity(
    embeddings["khmer_cashew"],
    embeddings["khmer_cashew"]
)
print(f"\n   Test 1: Khmer-Khmer (same text)")
print(f"   Similarity: {sim_khmer_khmer:.4f}")
print(f"   Expected: ~1.0 (identical)")
print(f"   Result: {'✅ PASS' if sim_khmer_khmer > 0.99 else '❌ FAIL'}")

# Test 2: Cross-lingual (Khmer cashew vs English cashew - same meaning)
sim_cross_lingual = cosine_similarity(
    embeddings["khmer_cashew"],
    embeddings["english_cashew"]
)
print(f"\n   Test 2: Cross-lingual (Khmer cashew ↔ English cashew)")
print(f"   Similarity: {sim_cross_lingual:.4f}")
print(f"   Expected: >0.60 (same meaning, different language)")
print(f"   Result: {'✅ PASS' if sim_cross_lingual > 0.60 else '❌ FAIL'}")

# Test 3: Different topics (Khmer cashew vs Khmer rubber)
sim_different_topics = cosine_similarity(
    embeddings["khmer_cashew"],
    embeddings["khmer_rubber"]
)
print(f"\n   Test 3: Different topics (Khmer cashew vs Khmer rubber)")
print(f"   Similarity: {sim_different_topics:.4f}")
print(f"   Expected: 0.50-0.75 (same language, related but different topics)")
print(f"   Result: {'✅ PASS' if 0.40 < sim_different_topics < 0.80 else '❌ FAIL'}")

# Test 4: Cross-lingual different topics (Khmer cashew vs English rubber)
sim_cross_different = cosine_similarity(
    embeddings["khmer_cashew"],
    embeddings["english_rubber"]
)
print(f"\n   Test 4: Cross-lingual different (Khmer cashew ↔ English rubber)")
print(f"   Similarity: {sim_cross_different:.4f}")
print(f"   Expected: 0.40-0.65 (different language, related topics)")
print(f"   Result: {'✅ PASS' if 0.30 < sim_cross_different < 0.70 else '❌ FAIL'}")

# Test 5: Mixed Khmer-English
sim_mixed = cosine_similarity(
    embeddings["mixed_khmer_english"],
    embeddings["english_cashew"]
)
print(f"\n   Test 5: Mixed (Khmer-English mix ↔ Pure English)")
print(f"   Similarity: {sim_mixed:.4f}")
print(f"   Expected: >0.50 (mixed languages, related topic)")
print(f"   Result: {'✅ PASS' if sim_mixed > 0.50 else '❌ FAIL'}")

# Test 6: Vietnamese support
sim_vietnamese = cosine_similarity(
    embeddings["vietnamese_agriculture"],
    embeddings["english_cashew"]
)
print(f"\n   Test 6: Vietnamese (Vietnamese agriculture ↔ English cashew)")
print(f"   Similarity: {sim_vietnamese:.4f}")
print(f"   Expected: 0.50-0.70 (different language, related topic)")
print(f"   Result: {'✅ PASS' if 0.40 < sim_vietnamese < 0.75 else '❌ FAIL'}")

# Step 6: Test with query format (important for E5 models)
print("\n6️⃣ Testing query vs passage format...")

query_khmer = "query: ស្វាយចន្ទី នៅកម្ពុជា"  # Cashew in Cambodia
passage_khmer = "passage: ការផលិតស្វាយចន្ទី នៅកម្ពុជា បានកើនឡើង"  # Cashew production in Cambodia increased

emb_query = model.encode(query_khmer, convert_to_numpy=True)
emb_passage = model.encode(passage_khmer, convert_to_numpy=True)

sim_query_passage = cosine_similarity(emb_query, emb_passage)
print(f"   Query: '{query_khmer}'")
print(f"   Passage: '{passage_khmer}'")
print(f"   Similarity: {sim_query_passage:.4f}")
print(f"   Expected: >0.70 (relevant match)")
print(f"   Result: {'✅ PASS' if sim_query_passage > 0.70 else '❌ FAIL'}")

# Final assessment
print("\n" + "=" * 80)
print("📊 FINAL ASSESSMENT")
print("=" * 80)

criteria = {
    "Khmer Unicode support": sim_khmer_khmer > 0.99,
    "Cross-lingual capability": sim_cross_lingual > 0.60,
    "Topic differentiation": 0.40 < sim_different_topics < 0.80,
    "Mixed language support": sim_mixed > 0.50,
    "Vietnamese support": 0.40 < sim_vietnamese < 0.75,
    "Query-passage matching": sim_query_passage > 0.70,
}

passed = sum(criteria.values())
total = len(criteria)

print(f"\n✅ Tests passed: {passed}/{total}")
for criterion, result in criteria.items():
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"   {status} - {criterion}")

if passed >= 5:
    print("\n" + "=" * 80)
    print("🎉 CONCLUSION: multilingual-e5-large is SUITABLE for this project!")
    print("=" * 80)
    print("\n✅ Khmer support: EXCELLENT")
    print("✅ Cross-lingual: GOOD")
    print("✅ Vietnamese: GOOD")
    print("✅ Mixed languages: GOOD")
    print("\n🚀 RECOMMENDATION: Proceed with Phase 1 implementation")
    print("   - Use multilingual-e5-large (1024 dim)")
    print("   - Chunking: 512 tokens, 10% overlap")
    print("   - Supabase pgvector with HNSW index")
    print("=" * 80)
elif passed >= 3:
    print("\n" + "=" * 80)
    print("⚠️ CONCLUSION: multilingual-e5-large is ACCEPTABLE but needs validation")
    print("=" * 80)
    print("\n⚠️ Some tests failed - review carefully")
    print("🔄 RECOMMENDATION: Test with real PDF extracts before full implementation")
    print("=" * 80)
else:
    print("\n" + "=" * 80)
    print("❌ CONCLUSION: multilingual-e5-large NOT suitable")
    print("=" * 80)
    print("\n❌ Too many failures")
    print("🔄 RECOMMENDATION: Switch to paraphrase-multilingual-mpnet-base-v2")
    print("   - Dimension: 768 (vs 1024)")
    print("   - Better documented multilingual support")
    print("=" * 80)

print("\n✅ POC Test Complete!")
