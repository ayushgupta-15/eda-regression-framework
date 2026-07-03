import yaml
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TestTarget:
    name: str
    run_cmd: str
    adapter: str
    timeout_s: int
    artifacts: List[str] = field(default_factory=list)
    repo_path: str = ""

@dataclass
class RepoConfig:
    name: str
    repo_path: str
    test_targets: List[TestTarget]
    build_cmd: Optional[str] = None

def load_config(yaml_path: str) -> RepoConfig:
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    targets = []
    for t_data in data.get('test_targets', []):
        target = TestTarget(
            name=t_data['name'],
            run_cmd=t_data['run_cmd'],
            adapter=t_data['adapter'],
            timeout_s=t_data.get('timeout_s', 30),
            artifacts=t_data.get('artifacts', []),
            repo_path=data['repo_path']
        )
        targets.append(target)
        
    return RepoConfig(
        name=data['name'],
        repo_path=data['repo_path'],
        build_cmd=data.get('build_cmd'),
        test_targets=targets
    )
