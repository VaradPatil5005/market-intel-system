"""
FRIDAY Master Voice & Multimodal Command Agent.

BACKWARD-COMPATIBILITY PROXY — do not add new logic here.

This module is a thin re-export shim for `agents/kim_voice_agent.py`.
It exists solely to preserve import paths that were written against the
original FRIDAY name (e.g. ``from agents.friday_voice_agent import
FridayVoiceAgent``) while the canonical implementation lives in
``agents/kim_voice_agent.py`` (KIM = Chief Female AI Market Strategist).

Naming history:
  v1: agent was called FridayVoiceAgent (inspired by Iron Man's FRIDAY).
  v2: renamed to KimVoiceAgent to align with the project's AI persona
      branding. friday_voice_agent.py was kept to avoid breaking callers.

Migration path:
  Replace ``from agents.friday_voice_agent import FridayVoiceAgent``
  with     ``from agents.kim_voice_agent import KimVoiceAgent``.
  Both are functionally identical; the Friday aliases will be removed
  in a future major version.
"""
from agents.kim_voice_agent import (
    KimResponse as FridayResponse,
    KimVoiceAgent as FridayVoiceAgent,
    kim_voice_agent as friday_voice_agent,
    KimResponse,
    KimVoiceAgent,
    kim_voice_agent,
)

__all__ = [
    "FridayResponse",
    "FridayVoiceAgent",
    "friday_voice_agent",
    "KimResponse",
    "KimVoiceAgent",
    "kim_voice_agent",
]
