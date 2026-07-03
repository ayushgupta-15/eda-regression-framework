from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ParseResult:
    passed: bool
    coverage: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

class ToolAdapter(ABC):
    @abstractmethod
    def parse(self, log_text: str) -> ParseResult:
        pass
