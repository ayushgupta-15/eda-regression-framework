import json
import os

def save_results(all_results, output_path="logs/results.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    data = []
    for config_name, targets_data in all_results.items():
        for target, result, parse_result in targets_data:
            passed = parse_result.passed and (result.exit_code == 0)
            data.append({
                'config_name': config_name,
                'target_name': target.name,
                'passed': passed,
                'duration_s': result.duration_s,
                'warnings': len(parse_result.warnings),
                'errors': parse_result.errors,
                'log_path': result.log_path
            })
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
