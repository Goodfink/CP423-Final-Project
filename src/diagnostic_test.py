import json
from pathlib import Path
from src.llm.llm_setup import HuggingFaceLLM
from src.evaluation.evaluation_metrics import EvaluationMetrics

evaluation_file = Path("src/evaluation/evaluation_set.json")
with open(evaluation_file) as f:
    evaluation_set = json.load(f)

diagnostic_items = [item for item in evaluation_set if item["question_type"] == "factoid"]

llm = HuggingFaceLLM()
metrics = EvaluationMetrics()
output_file = Path("evaluation_results.json")
if output_file.exists():
    with open(output_file) as f:
        saved_results = {item["question_id"]: item for item in json.load(f)}
else:
    saved_results = {}

for i, question_item in enumerate(diagnostic_items, 1):
    q = question_item["question"]
    print(f"[{i}/10] Q: {q}")
    
    try:
        diagnostic_prompt = f"""Answer the question briefly.
If you do not know, say "I don't know."

Question: {q}
Answer:"""
        answer = llm.generate(diagnostic_prompt, max_tokens=80, temperature=0.0)
        
        if answer and len(answer.strip()) > 0:
            result_text = answer
        else:
            result_text = "No answer generated"
            
    except Exception as e:
        result_text = f"Error: {str(e)[:50]}"
    
    evaluation = metrics.evaluate_answer(
        result_text,
        question_item["ground_truth_answer"],
        question_item["question_type"],
        [],
        question_item.get("required_answer_terms"),
        question_item.get("forbidden_answer_terms"),
        require_citations=False
    )
    saved_result = saved_results.get(question_item["question_id"], {})
    manual_correct = saved_result.get("no_retrieval", {}).get("manual_correct")
    saved_result.update({
        "question_id": question_item["question_id"],
        "question": q,
        "question_type": question_item["question_type"],
        "no_retrieval": {
            "answer": result_text,
            "correct": evaluation["correct"],
            "citations_accurate": evaluation["citations_accurate"],
            "manual_correct": manual_correct
        }
    })
    saved_results[question_item["question_id"]] = saved_result
    print(f"    A: {result_text}\n")

results = [saved_results[item["question_id"]] for item in evaluation_set if item["question_id"] in saved_results]
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

automatic_correct = sum(saved_results[item["question_id"]]["no_retrieval"]["correct"] for item in diagnostic_items)
print(f"Automatic accuracy: {automatic_correct}/{len(diagnostic_items)} ({automatic_correct / len(diagnostic_items):.1%})")
print(f"Results saved to: {output_file}")
