# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def run(self, state) -> Any:
        pass
    
    def log(self, message: str, level: str = "info"):
        getattr(self.logger, level, self.logger.info)(f"[{self.name}] {message}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)