# src/utils/multilingual.py
from typing import Dict, Any

class Translator:
    """Simple multilingual translator stub"""
    
    def translate(self, text: str, target_lang: str) -> str:
        """Translate text to target language"""
        # For now, just return the same text
        # In production, integrate with a translation API
        return text

translator = Translator()