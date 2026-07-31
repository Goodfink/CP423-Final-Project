import json
import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.bm25 import BM25Retriever, load_corpus as load_bm25_corpus
from src.retrieval.dense_retrieval import DenseRetriever, load_corpus as load_dense_corpus
from src.llm.llm_setup import HuggingFaceLLM
from src.llm.answer_generation import RAGPipeline, generate_with_both_retrievers
from src.evaluation.evaluation_metrics import EvaluationMetrics

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
EVAL_DIR = PROJECT_ROOT / "src" / "evaluation"
RESULTS_FILE = PROJECT_ROOT / "evaluation_results.json"

def load_evaluation_set():
    """Load evaluation questions"""
    eval_file = EVAL_DIR / "evaluation_set.json"
    with open(eval_file, "r") as f:
        return json.load(f)

def setup_system():
    """Initialize retrieval and LLM systems"""
    # Load corpus
    corpus_path = DATA_DIR / "advisories.jsonl"
    records = load_bm25_corpus(corpus_path)

    # Setup BM25
    print("\n2. Setting up BM25 retriever...")
    bm25 = BM25Retriever()
    bm25.build_index(records)

    # Setup Dense Retriever
    print("\n3. Setting up Dense retriever...")
    dense = DenseRetriever()
    dense.build_index(records)

    # Setup LLM
    print("\n4. Loading LLM (this takes 2-3 minutes on first run)...")
    try:
        llm = HuggingFaceLLM()
    except Exception as e:
        print(f"   ✗ LLM Error: {e}")
        return None, None, None, None
    
    return bm25, dense, llm, records

def test_single_query(question, bm25, dense, llm):
    """Test a single query with both retrievers"""
    print(f"\nQuestion: {question}\n")
    
    pipeline = RAGPipeline(bm25, dense, llm)
    
    # BM25 result
    print("BM25 Results:")
    bm25_result = pipeline.generate_answer(question, use_dense=False, top_k=5)
    print(f"  Top chunk: {bm25_result['retrieved_chunks'][0]['document_id']}")
    print(f"  Score: {bm25_result['retrieved_chunks'][0]['score']:.4f}")
    
    # Dense result
    print("\nDense Retrieval Results:")
    dense_result = pipeline.generate_answer(question, use_dense=True, top_k=5)
    print(f"  Top chunk: {dense_result['retrieved_chunks'][0]['document_id']}")
    print(f"  Score: {dense_result['retrieved_chunks'][0]['score']:.4f}")
    
    # Show answers
    print("\nBM25 Answer:")
    print(f"  {bm25_result['answer'][:200]}...")
    
    print("\nDense Answer:")
    print(f"  {dense_result['answer'][:200]}...")

def run_full_evaluation(bm25, dense, llm):
    """Run evaluation on all test questions"""
    
    evaluation_set = load_evaluation_set()
    metrics = EvaluationMetrics()
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            saved_results = {item["question_id"]: item for item in json.load(f)}
    else:
        saved_results = {}
    
    bm25_results = []
    dense_results = []
    
    for i, question_item in enumerate(evaluation_set, 1):
        print(f"\n[{i}/{len(evaluation_set)}] {question_item['question'][:60]}...")
        
        # Generate with both methods
        result = generate_with_both_retrievers(
            question_item['question'],
            bm25, dense, llm
        )
        
        # Evaluate both
        bm25_eval = metrics.evaluate_answer(
            result['bm25']['answer'],
            question_item['ground_truth_answer'],
            question_item['question_type'],
            question_item['ground_truth_chunk_ids'],
            question_item.get('required_answer_terms'),
            question_item.get('forbidden_answer_terms')
        )
        
        dense_eval = metrics.evaluate_answer(
            result['dense']['answer'],
            question_item['ground_truth_answer'],
            question_item['question_type'],
            question_item['ground_truth_chunk_ids'],
            question_item.get('required_answer_terms'),
            question_item.get('forbidden_answer_terms')
        )
        
        bm25_results.append(bm25_eval)
        dense_results.append(dense_eval)

        saved_result = saved_results.get(question_item["question_id"], {})
        saved_result.update({
            "question_id": question_item["question_id"],
            "question": question_item["question"],
            "question_type": question_item["question_type"],
            "bm25": {
                "answer": result["bm25"]["answer"],
                "correct": bm25_eval["correct"],
                "citations_accurate": bm25_eval["citations_accurate"],
                "retrieved_document_ids": [item["document_id"] for item in result["bm25"]["retrieved_chunks"]]
            },
            "dense": {
                "answer": result["dense"]["answer"],
                "correct": dense_eval["correct"],
                "citations_accurate": dense_eval["citations_accurate"],
                "retrieved_document_ids": [item["document_id"] for item in result["dense"]["retrieved_chunks"]]
            }
        })
        saved_results[question_item["question_id"]] = saved_result
        
        # Print status
        bm25_status = "✓" if bm25_eval["correct"] else "✗"
        dense_status = "✓" if dense_eval["correct"] else "✗"
        print(f"  BM25: {bm25_status} | Dense: {dense_status}")

    ordered_results = [saved_results[item["question_id"]] for item in evaluation_set]
    with open(RESULTS_FILE, "w") as f:
        json.dump(ordered_results, f, indent=2)
    
    bm25_stats = metrics.aggregate_results(bm25_results)
    dense_stats = metrics.aggregate_results(dense_results)
    
    print(f"\nBM25 Results:")
    print(f"  Accuracy: {bm25_stats['accuracy']:.1%} ({bm25_stats['correct_answers']}/{bm25_stats['total_questions']})")
    print(f"  Factoid Accuracy: {bm25_stats['breakdown']['factoid']['accuracy']:.1%} ({bm25_stats['breakdown']['factoid']['correct']}/{bm25_stats['breakdown']['factoid']['count']})")
    print(f"  Citation Accuracy: {bm25_stats['citation_accuracy']:.1%}")
    if bm25_stats['breakdown']['unanswerable']['count'] > 0:
        print(f"  'I don't know' Accuracy: {bm25_stats['idontknow_accuracy']:.1%}")
    
    print(f"\nDense Retrieval Results:")
    print(f"  Accuracy: {dense_stats['accuracy']:.1%} ({dense_stats['correct_answers']}/{dense_stats['total_questions']})")
    print(f"  Factoid Accuracy: {dense_stats['breakdown']['factoid']['accuracy']:.1%} ({dense_stats['breakdown']['factoid']['correct']}/{dense_stats['breakdown']['factoid']['count']})")
    print(f"  Citation Accuracy: {dense_stats['citation_accuracy']:.1%}")
    if dense_stats['breakdown']['unanswerable']['count'] > 0:
        print(f"  'I don't know' Accuracy: {dense_stats['idontknow_accuracy']:.1%}")
    
    # Comparison
    print(f"\nComparison:")
    diff = (dense_stats['accuracy'] - bm25_stats['accuracy']) * 100
    print(f"  Dense vs BM25: {diff:+.1f}% accuracy")
    print(f"  Results saved to: {RESULTS_FILE}")
    
    return bm25_results, dense_results

def interactive_demo(bm25, dense, llm):
    """Interactive Q&A demo"""
    print("Ask questions about vulnerabilities. Type 'exit' to quit.\n")
    
    pipeline = RAGPipeline(bm25, dense, llm)
    
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() == 'exit':
            break
        
        if not question:
            continue
        
        # Generate answer with dense retrieval
        result = pipeline.generate_answer(question, use_dense=True, top_k=5)
        
        print(f"\nAnswer: {result['answer']}")
        print(f"\nSources:")
        for chunk in result['retrieved_chunks'][:3]:
            print(f"  - {chunk['document_id']}: {chunk['summary']}")

def main():
    parser = argparse.ArgumentParser(description='Test RAG System')
    parser.add_argument('--test-setup', action='store_true', help='Test system setup only')
    parser.add_argument('--query', type=str, help='Test single query')
    parser.add_argument('--evaluate', choices=['all', 'sample'], help='Run evaluation')
    parser.add_argument('--demo', action='store_true', help='Interactive demo')
    
    args = parser.parse_args()
    
    # Setup system
    bm25, dense, llm, records = setup_system()
    
    if bm25 is None:
        sys.exit(1)
    
    # Test setup only
    if args.test_setup:
        return
    
    # Test single query
    if args.query:
        test_single_query(args.query, bm25, dense, llm)
        return
    
    # Run evaluation
    if args.evaluate == 'all':
        run_full_evaluation(bm25, dense, llm)
        return
    
    # Interactive demo
    if args.demo:
        interactive_demo(bm25, dense, llm)
        return
    
    # Default: show help
    parser.print_help()

if __name__ == "__main__":
    main()