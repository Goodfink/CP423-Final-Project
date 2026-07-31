import json
import re
from pathlib import Path

class EvaluationMetrics:
    def __init__(self):
        self.results = []
    
    def extract_citations(self, answer_text):
        """Extract citation IDs from answer"""
        citations = re.findall(r'\[(GHSA-[^\]]+|GO-[^\]]+|CVE-[^\]]+)\]', answer_text)
        return set(citations)
    
    def check_contains_idontknow(self, answer_text):
        """Check if answer appropriately says 'I don't know'"""
        answer_lower = answer_text.lower()
        return "i don't know" in answer_lower or "don't know" in answer_lower
    
    def evaluate_citation_accuracy(self, cited_ids, ground_truth_ids):
        """Check if citations match ground truth"""
        if not ground_truth_ids:
            # For unanswerable questions, should have no citations
            return len(cited_ids) == 0
        
        if not cited_ids:
            return False
        
        # Check if any cited ID matches ground truth
        cited_set = set(cited_ids)
        truth_set = set(ground_truth_ids)
        
        # At least one citation should match
        return bool(cited_set & truth_set)
    
    def evaluate_answer(self, generated_answer, ground_truth_answer, question_type, ground_truth_chunk_ids):
        """Evaluate a single answer"""
        
        result = {
            "answer_text": generated_answer,
            "ground_truth": ground_truth_answer,
            "question_type": question_type,
            "correct": False,
            "has_appropriate_idontknow": False,
            "citations_accurate": False,
            "notes": []
        }
        
        # For unanswerable questions
        if question_type == "unanswerable":
            if self.check_contains_idontknow(generated_answer):
                result["correct"] = True
                result["has_appropriate_idontknow"] = True
                result["notes"].append("Correctly indicated information not available")
            else:
                result["notes"].append("Should have said 'I don't know'")
            
            # Should have no citations for unanswerable
            cited_ids = self.extract_citations(generated_answer)
            result["citations_accurate"] = len(cited_ids) == 0
            if len(cited_ids) > 0:
                result["notes"].append(f"Incorrectly cited: {cited_ids}")
            
            return result
        
        # For factoid and multi-hop questions
        cited_ids = self.extract_citations(generated_answer)
        
        # Check citations
        if ground_truth_chunk_ids:
            citations_match = any(
                cid in ground_truth_chunk_ids 
                for cid in cited_ids
            )
            result["citations_accurate"] = citations_match
            
            if not citations_match and cited_ids:
                result["notes"].append(f"Citations don't match. Expected from {ground_truth_chunk_ids}, got {cited_ids}")
        
        # Basic correctness check (word overlap)
        ground_words = set(ground_truth_answer.lower().split())
        answer_words = set(generated_answer.lower().split())
        
        overlap = ground_words & answer_words
        if len(overlap) > 2:
            result["correct"] = True
            result["notes"].append(f"Answer contains key terms from ground truth")
        else:
            result["notes"].append("Answer doesn't match ground truth")
        
        return result
    
    def aggregate_results(self, all_results):
        """Aggregate evaluation results"""
        
        total = len(all_results)
        if total == 0:
            return {}
        
        correct = sum(1 for r in all_results if r["correct"])
        citations_accurate = sum(1 for r in all_results if r["citations_accurate"])
        appropriate_idontknow = sum(1 for r in all_results if r["has_appropriate_idontknow"])
        
        unanswerable_count = sum(1 for r in all_results if r["question_type"] == "unanswerable")
        factoid_count = sum(1 for r in all_results if r["question_type"] == "factoid")
        multihop_count = sum(1 for r in all_results if r["question_type"] == "multi-hop")
        
        return {
            "total_questions": total,
            "correct_answers": correct,
            "accuracy": correct / total if total > 0 else 0,
            "citation_accuracy": citations_accurate / (total - unanswerable_count) if (total - unanswerable_count) > 0 else 0,
            "idontknow_accuracy": appropriate_idontknow / unanswerable_count if unanswerable_count > 0 else 0,
            "breakdown": {
                "factoid": {"count": factoid_count},
                "multi_hop": {"count": multihop_count},
                "unanswerable": {"count": unanswerable_count}
            }
        }