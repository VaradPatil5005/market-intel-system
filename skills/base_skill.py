"""
Base class for Hermes-Agent inspired Market Skills.
Each skill encapsulates a specific institutional strategy playbook,
execution trigger rules, and dynamic self-learning accuracy tracking.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseMarketSkill(ABC):
    """Abstract base class for executable institutional market skills."""

    name: str = "base_skill"
    description: str = "Base market skill playbook"
    category: str = "GENERAL"
    initial_weight: float = 1.0

    def __init__(self):
        self.weight: float = self.initial_weight
        self.invocations: int = 0
        self.successful_outcomes: int = 0

    @abstractmethod
    def evaluate_trigger(self, market_context: Dict[str, Any]) -> bool:
        """Determines whether current market conditions warrant this skill's activation."""
        pass

    @abstractmethod
    def execute(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the skill playbook and returns actionable institutional recommendations."""
        pass

    def record_feedback(self, outcome_accuracy: float):
        """
        Self-learning update: adapts skill weight based on post-execution outcome accuracy.
        outcome_accuracy: float between 0.0 (total failure) and 1.0 (perfect prediction/hedge).
        """
        self.invocations += 1
        if outcome_accuracy >= 0.6:
            self.successful_outcomes += 1
            self.weight = min(2.5, self.weight + 0.05)
        else:
            self.weight = max(0.2, self.weight - 0.08)

    @property
    def win_rate(self) -> float:
        if self.invocations == 0:
            return 1.0
        return self.successful_outcomes / self.invocations
