"""Base prompt template system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class PromptTemplate(ABC, Generic[T]):
    """Base class for all prompt templates.

    Provides:
    - Version tracking
    - Variable interpolation
    - Validation
    - Serialization
    """

    version: str = "1.0.0"
    language: str = "en"

    @abstractmethod
    def render(self, **kwargs: Any) -> str:
        """Render the prompt with provided variables."""
        pass

    @abstractmethod
    def validate_inputs(self, **kwargs: Any) -> None:
        """Validate that all required variables are provided."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Serialize template metadata."""
        return {
            "version": self.version,
            "language": self.language,
            "template_type": self.__class__.__name__,
        }
