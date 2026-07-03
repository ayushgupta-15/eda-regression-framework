import re
from src.adapters.tool_adapter import ToolAdapter, ParseResult

class GenericRegexAdapter(ToolAdapter):
    def __init__(self, pass_pattern: str, fail_pattern: str = r"ERROR"):
        self.pass_pattern = re.compile(pass_pattern, re.IGNORECASE) if pass_pattern else None
        self.fail_pattern = re.compile(fail_pattern, re.IGNORECASE) if fail_pattern else None

    def parse(self, log_text: str) -> ParseResult:
        passed = False
        if self.pass_pattern:
            passed = bool(self.pass_pattern.search(log_text))
        else:
            passed = True
            
        errors = []
        if self.fail_pattern:
            errors = self.fail_pattern.findall(log_text)
            if errors:
                passed = False
                
        warnings = re.findall(r"WARNING:.*", log_text, re.IGNORECASE)
        
        return ParseResult(
            passed=passed,
            errors=[str(e) for e in errors],
            warnings=warnings
        )
