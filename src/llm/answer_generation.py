import re
from src.llm.prompt_template import create_rag_prompt
from src.llm.llm_setup import HuggingFaceLLM

class RAGPipeline:
    def __init__(self, bm25_retriever, dense_retriever, llm=None):
        """Initialize RAG pipeline"""
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever
        self.llm = llm or HuggingFaceLLM()
    
    def generate_answer(self, question, use_dense=True, top_k=5):
        """Generate answer using retrieved context"""
        
        # Retrieve context
        if use_dense:
            retrieved = self.dense_retriever.search(question, top_k=top_k)
            retrieval_method = "dense"
        else:
            retrieved = self.bm25_retriever.search(question, top_k=top_k)
            retrieval_method = "bm25"
        
        # Get full records for context
        retrieved_chunks = [r['record'] for r in retrieved]
        
        # Create prompt
        prompt = create_rag_prompt(question, retrieved_chunks)
        
        # Generate answer
        answer = self.llm.generate(prompt, temperature=0.3, max_tokens=300)
        
        return {
            "question": question,
            "answer": answer,
            "retrieved_chunks": retrieved,
            "retrieval_method": retrieval_method,
            "num_chunks": len(retrieved)
        }
    
    def extract_citations(self, answer_text):
        """Extract citation IDs from answer"""
        # Find all [GHSA-...] or [GO-...] patterns
        citations = re.findall(r'\[(GHSA-[^\]]+|GO-[^\]]+|CVE-[^\]]+)\]', answer_text)
        return list(set(citations))  # Remove duplicates

def generate_with_both_retrievers(question, bm25_retriever, dense_retriever, llm):
    """Generate answers with both retrieval methods for comparison"""
    
    pipeline = RAGPipeline(bm25_retriever, dense_retriever, llm)
    
    bm25_result = pipeline.generate_answer(question, use_dense=False, top_k=5)
    dense_result = pipeline.generate_answer(question, use_dense=True, top_k=5)
    
    return {
        "question": question,
        "bm25": bm25_result,
        "dense": dense_result
    }