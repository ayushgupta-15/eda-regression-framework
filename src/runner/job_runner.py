import subprocess
import time
import os
from dataclasses import dataclass
from src.runner.target_config import TestTarget

@dataclass
class JobResult:
    name: str
    exit_code: int
    log_path: str
    duration_s: float

def write_log(target_name: str, stdout: str, stderr: str) -> str:
    os.makedirs('logs', exist_ok=True)
    log_path = f'logs/{target_name}.log'
    with open(log_path, 'w') as f:
        f.write("=== STDOUT ===\n")
        f.write(stdout)
        f.write("\n=== STDERR ===\n")
        f.write(stderr)
    return log_path

def run_job(target: TestTarget) -> JobResult:
    start = time.monotonic()
    
    # repo_path is relative to where we run the CLI, we can make it absolute
    repo_path = os.path.abspath(target.repo_path)
    
    try:
        result = subprocess.run(
            target.run_cmd, shell=True, cwd=repo_path,
            capture_output=True, text=True, timeout=target.timeout_s
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as e:
        exit_code = -1
        stdout = e.stdout.decode('utf-8') if e.stdout else ""
        stderr = e.stderr.decode('utf-8') if e.stderr else f"Timeout after {target.timeout_s}s"

    duration_s = time.monotonic() - start
    log_path = write_log(target.name, stdout, stderr)
    return JobResult(
        name=target.name,
        exit_code=exit_code,
        log_path=log_path,
        duration_s=duration_s
    )
