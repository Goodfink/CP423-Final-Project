import json
from pathlib import Path
from llm.llm_setup import HuggingFaceLLM

diagnostic_questions = [
    "What is CVE-2020-29244?",
    "Which Go package had an out-of-bounds read vulnerability?",
    "What is GHSA-28q9-9c3g-v3f9?",
    "What ecosystem has npm advisories?",
    "What does BM25 stand for?",
    "How many advisories are in the corpus?",
    "What is lakeFS?",
    "When was the dhowden tag vulnerability published?",
    "What is the fix for the dhowden tag panic?",
    "Which package manager is related to Python?"
]

print("=" * 60)
print("DIAGNOSTIC TEST: LLM WITHOUT RETRIEVED CONTEXT")
print("=" * 60)

llm = HuggingFaceLLM()

print("\nLoading LLM...")
print("Testing questions WITHOUT any retrieved context\n")

results = []

for i, q in enumerate(diagnostic_questions, 1):
    print(f"[{i}/10] Q: {q}")
    
    try:
        # Generate answer with timeout and error handling
        answer = llm.generate(q, max_tokens=80, temperature=0.5)
        
        if answer and len(answer.strip()) > 0:
            result_text = answer[:120]
        else:
            result_text = "No answer generated"
            
    except Exception as e:
        result_text = f"Error: {str(e)[:50]}"
    
    result = {
        "question": q,
        "answer": result_text,
        "manual_correct": None  # You fill this in manually
    }
    results.append(result)
    print(f"    A: {result_text}\n")

# Save results for manual review
output_file = Path("diagnostic_results.json")
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print("=" * 60)
print(f"Results saved to: {output_file}")
print("=" * 60)
print("\n📝 NEXT STEP:")
print("1. Open diagnostic_results.json")
print("2. For each answer, manually add 'manual_correct': true or false")
print("3. Count total correct answers")
print("4. Report in your project: 'Without retrieval: X/10 correct'")
print("5. Compare to WITH retrieval: 12/15 (80%) to show improvement")