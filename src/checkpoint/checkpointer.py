import json
from pathlib import Path
from typing import Any, Dict, Optional


class SessionCheckpointer:
    """Simple JSON-backed checkpoint manager for session state."""

    def __init__(self, base_dir: str = "logs/checkpoints"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session_id: str, state: Dict[str, Any]) -> str:
        checkpoint_path = self.base_dir / f"{session_id}.json"
        payload = {
            "session_id": session_id,
            "state": state,
        }
        checkpoint_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return str(checkpoint_path)

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        checkpoint_path = self.base_dir / f"{session_id}.json"
        if not checkpoint_path.exists():
            return None
        try:
            data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            return data.get("state")
        except Exception:
            return None

    def delete(self, session_id: str) -> bool:
        checkpoint_path = self.base_dir / f"{session_id}.json"
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            return True
        return False
