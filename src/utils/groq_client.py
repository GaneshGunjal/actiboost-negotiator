# src/utils/groq_client.py
import os
import sys
import json
import httpx
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from pathlib import Path

# Load .env manually
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    print(f"📁 Loading .env from: {env_path}")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                except ValueError:
                    pass

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        print(f"🔑 GROQ_API_KEY: {'✅ SET' if self.api_key else '❌ NOT SET'}")
        
        if not self.api_key:
            # Try reading directly from .env file
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'GROQ_API_KEY' in line and not line.startswith('#'):
                            self.api_key = line.split('=', 1)[1].strip()
                            print(f"✅ Found GROQ_API_KEY: {self.api_key[:20]}...")
                            break
            except Exception as e:
                print(f"❌ Error reading .env: {e}")
            
            if not self.api_key:
                raise ValueError("GROQ_API_KEY not set! Please check your .env file.")
        
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
        
        logger.info(f"GROQ client initialized with model: {self.model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def ask(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": 4096
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"GROQ API error: {response.text}")
    
    async def ask_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        response = await self.ask(prompt, system_prompt)
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"error": "Could not parse JSON", "content": response}

# Create global instance
print("🔄 Creating GROQ client...")
groq = GroqClient()
print("✅ GROQ client ready")