import re
from src.adapters.tool_adapter import ToolAdapter, ParseResult

class IcarusAdapter(ToolAdapter):
    def parse(self, log_text: str) -> ParseResult:
        # Match testbenches' actual output
        passed = "ALL TESTS PASSED" in log_text
        
        coverage = None
        warnings = re.findall(r"WARNING:.*", log_text, re.IGNORECASE)
        errors = re.findall(r"ERROR:.*", log_text, re.IGNORECASE)
        
        return ParseResult(
            passed=passed,
            coverage=coverage,
            warnings=warnings,
            errors=errors
        )
