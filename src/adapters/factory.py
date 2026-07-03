from src.adapters.tool_adapter import ToolAdapter
from src.adapters.icarus_adapter import IcarusAdapter
from src.adapters.generic_adapter import GenericRegexAdapter

def get_adapter(name: str) -> ToolAdapter:
    if name.lower() == 'icarus':
        return IcarusAdapter()
    elif name.lower() == 'generic':
        return GenericRegexAdapter(pass_pattern=r"PASS|PASSED|SUCCESS|completed|successfully", fail_pattern=r"FAIL|ERROR")
    else:
        raise ValueError(f"Unknown adapter: {name}")
