"""
Hermes-Agent Inspired Bounded Persistent Memory Store.
Maintains curated long-term memory (MEMORY.md) and user profile (USER.md)
with bounded character limits and system prompt snapshot serialization.
"""

import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional

MEMORY_DIR = Path("storage/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = MEMORY_DIR / "MEMORY.md"
USER_FILE = MEMORY_DIR / "USER.md"

MAX_MEMORY_CHARS = 2200
MAX_USER_CHARS = 1375

DEFAULT_MEMORY = """# INSTITUTIONAL MARKET KNOWLEDGE & ALPHA RULES
NVDA earnings runups have demonstrated 82% call skew with implied volatility expansion.
Hormuz chokepoint disruptions add an estimated $3.20/bbl geopolitical risk premium to Brent crude.
Taiwan Strait tension scores above 75.0 mandate direct hedging on advanced semiconductor foundries (<3nm).
Never execute block orders exceeding 0.5% Average Daily Volume via aggressive marketable orders; mandate TWAP/VWAP.
SEC 10-Q Segment Disclosure divergences exceeding 2.0% trigger automated confidence penalties on PR statements."""

DEFAULT_USER = """# USER PROFILE & MANDATES
Design System: Pitch-black Blackbox.ai institutional interface (#080808 with #ff5500 accents).
Zero Emoji Mandate: Strict prohibition on emojis in all UI elements, logs, reports, and code outputs.
Risk Budget: Value-at-Risk (95% 1-Day) threshold capped at 3.0% notional portfolio value.
Execution Mode: Interactive multi-agent surveillance with voice synthesis biometrics."""

_lock = threading.Lock()

class BoundedMemoryStore:
    """Thread-safe manager for bounded persistent markdown memory stores."""

    def __init__(self):
        self._ensure_files()

    def _ensure_files(self):
        with _lock:
            if not MEMORY_FILE.exists():
                MEMORY_FILE.write_text(DEFAULT_MEMORY.strip(), encoding="utf-8")
            if not USER_FILE.exists():
                USER_FILE.write_text(DEFAULT_USER.strip(), encoding="utf-8")

    def get_content(self, store: str = "MEMORY") -> str:
        filepath = MEMORY_FILE if store.upper() == "MEMORY" else USER_FILE
        with _lock:
            if filepath.exists():
                return filepath.read_text(encoding="utf-8")
            return ""
    def read_memory(self) -> str:
        """Read long-term institutional memory content."""
        return self.get_content("MEMORY")

    def read_user(self) -> str:
        """Read user profile and mandates content."""
        return self.get_content("USER")


    def get_stats(self, store: str = "MEMORY") -> Dict[str, Any]:
        content = self.get_content(store)
        limit = MAX_MEMORY_CHARS if store.upper() == "MEMORY" else MAX_USER_CHARS
        chars = len(content)
        pct = (chars / limit) * 100.0
        return {
            "store": store.upper(),
            "char_count": chars,
            "max_chars": limit,
            "percent_used": round(pct, 1),
            "available_chars": max(0, limit - chars)
        }

    def save_content(self, store: str, content: str) -> bool:
        limit = MAX_MEMORY_CHARS if store.upper() == "MEMORY" else MAX_USER_CHARS
        if len(content) > limit:
            raise ValueError(f"Content length ({len(content)}) exceeds maximum allowable limit of {limit} characters.")

        filepath = MEMORY_FILE if store.upper() == "MEMORY" else USER_FILE
        with _lock:
            filepath.write_text(content.strip(), encoding="utf-8")
        return True

    def append_entry(self, store: str, entry: str) -> bool:
        current = self.get_content(store)
        new_text = f"{current}\n{entry.strip()}"
        return self.save_content(store, new_text)

    def render_system_prompt_block(self) -> str:
        mem_stats = self.get_stats("MEMORY")
        user_stats = self.get_stats("USER")

        mem_body = self.get_content("MEMORY")
        user_body = self.get_content("USER")

        divider = "=" * 60
        return (
            f"\n{divider}\n"
            f"HERMES PERSISTENT MEMORY [{mem_stats['percent_used']}% - {mem_stats['char_count']}/{mem_stats['max_chars']} chars]\n"
            f"{divider}\n"
            f"{mem_body}\n"
            f"\n{divider}\n"
            f"USER PROFILE & CONSTRAINTS [{user_stats['percent_used']}% - {user_stats['char_count']}/{user_stats['max_chars']} chars]\n"
            f"{divider}\n"
            f"{user_body}\n"
            f"{divider}\n"
        )

memory_store = BoundedMemoryStore()
