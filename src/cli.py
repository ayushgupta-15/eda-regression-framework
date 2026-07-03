import argparse
import sys
import os
import concurrent.futures
import glob
import shutil
from src.runner.target_config import load_config
from src.runner.job_runner import run_job
from src.adapters.factory import get_adapter
from src.report.aggregator import save_results
from src.report.html_report import generate_html

def run_target(target):
    print(f"  -> Started {target.name}...")
    result = run_job(target)
    adapter = get_adapter(target.adapter)
    with open(result.log_path, 'r') as f:
        log_text = f.read()
    parse_result = adapter.parse(log_text)
    print(f"  -> Finished {target.name} in {result.duration_s:.2f}s")
    return (target, result, parse_result)

def print_summary(config_name, run_data):
    run_data.sort(key=lambda x: x[0].name)

    print("\n" + "="*80)
    print(f" REGRESSION SUMMARY: {config_name}")
    print("="*80)
    print(f"{'TARGET':<30} | {'STATUS':<10} | {'DURATION':<10} | {'WARNINGS':<10} | {'ERRORS':<10}")
    print("-" * 80)
    
    all_passed = True
    for target, result, parse_result in run_data:
        passed = parse_result.passed and (result.exit_code == 0)
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
            
        warnings_count = len(parse_result.warnings)
        errors_count = len(parse_result.errors)
        
        print(f"{target.name:<30} | {status:<10} | {result.duration_s:<8.2f}s | {warnings_count:<10} | {errors_count:<10}")

    print("="*80)
    return all_passed

def run_config(config_path: str):
    print(f"\nLoading config: {config_path}")
    if not os.path.exists(config_path):
        print(f"Error: Config file {config_path} not found.")
        return None, [], False
        
    config = load_config(config_path)
    print(f"Running targets for {config.name} in parallel...")
    
    run_data = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(run_target, target): target for target in config.test_targets}
        for future in concurrent.futures.as_completed(futures):
            try:
                run_data.append(future.result())
            except Exception as exc:
                print(f"Target generated an exception: {exc}")
                
    success = print_summary(config.name, run_data)
    return config.name, run_data, success

def main():
    parser = argparse.ArgumentParser(description="EDA Regression Framework")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    run_parser = subparsers.add_parser("run", help="Run one target set")
    run_parser.add_argument("config", help="Path to YAML config file")
    
    run_all_parser = subparsers.add_parser("run-all", help="Run all target sets")
    run_all_parser.add_argument("--dir", default="configs", help="Directory containing config files")
    
    report_parser = subparsers.add_parser("report", help="Regenerate HTML report from last run")
    clean_parser = subparsers.add_parser("clean", help="Clear old logs and reports")
    
    args = parser.parse_args()
    
    if args.command == "run":
        config_name, run_data, success = run_config(args.config)
        if config_name:
            all_results = {config_name: run_data}
            save_results(all_results)
            generate_html("logs/results.json", "reports/index.html")
        if not success:
            sys.exit(1)
            
    elif args.command == "run-all":
        config_files = glob.glob(os.path.join(args.dir, "*.yaml"))
        if not config_files:
            print(f"No config files found in {args.dir}")
            sys.exit(1)
            
        all_success = True
        all_results = {}
        for config_path in config_files:
            config_name, run_data, success = run_config(config_path)
            if config_name:
                all_results[config_name] = run_data
            if not success:
                all_success = False
                
        save_results(all_results)
        generate_html("logs/results.json", "reports/index.html")
        
        if not all_success:
            print("\nResult: SOME CONFIGS FAILED")
            sys.exit(1)
        else:
            print("\nResult: ALL CONFIGS PASSED")
            
    elif args.command == "report":
        generate_html("logs/results.json", "reports/index.html")
        
    elif args.command == "clean":
        if os.path.exists("logs"):
            shutil.rmtree("logs")
            print("Removed logs directory.")
        if os.path.exists("reports"):
            shutil.rmtree("reports")
            print("Removed reports directory.")
    else:
        print(f"Command not implemented: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    main()
