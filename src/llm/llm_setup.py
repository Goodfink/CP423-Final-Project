from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class HuggingFaceLLM:
    def __init__(self, model_name='distilgpt2'):
        """Initialize with a very small, fast model"""
        self.model_name = model_name
        
        print(f"Loading model: {model_name}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            print(f"✓ Model loaded successfully")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise RuntimeError(f"Failed to load model: {e}")
    
    def generate(self, prompt, temperature=0.3, max_tokens=150):
        """Generate response - fast and simple"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response.replace(prompt, "").strip()
        
        except Exception as e:
            print(f"Error: {e}")
            return None


# Legacy Ollama support
class OllamaLLM:
    def __init__(self, model_name='llama2:7b', host='http://localhost:11434'):
        import requests
        self.model_name = model_name
        self.host = host
        self.endpoint = f"{host}/api/generate"
        self._check_connection()
    
    def _check_connection(self):
        import requests
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✓ Connected to Ollama at {self.host}")
                return True
        except requests.ConnectionError:
            raise RuntimeError("Ollama not running")
    
    def generate(self, prompt, temperature=0.3, max_tokens=500):
        import requests
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        }
        try:
            response = requests.post(self.endpoint, json=payload, timeout=120)
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            print(f"Error: {e}")
            return None