import os
import json
import datetime
import subprocess

def get_git_info():
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
        return commit, branch
    except Exception:
        return "unknown", "unknown"

def generate_html(json_data_path: str, output_path: str):
    if not os.path.exists(json_data_path):
        print(f"Error: No run data found at {json_data_path}")
        return False
        
    with open(json_data_path, 'r') as f:
        runs = json.load(f)
        
    # Aggregate data by repository (config_name)
    repos = {}
    total_tests = len(runs)
    total_passed = 0
    total_duration = 0.0
    total_warnings = 0
    
    for run in runs:
        repo = run['config_name']
        if repo not in repos:
            repos[repo] = {'tests': 0, 'passed': 0, 'failed': 0, 'duration': 0.0, 'warnings': 0, 'runs': []}
            
        repos[repo]['tests'] += 1
        repos[repo]['duration'] += run['duration_s']
        repos[repo]['warnings'] += run['warnings']
        repos[repo]['runs'].append(run)
        
        total_duration += run['duration_s']
        total_warnings += run['warnings']
        
        if run['passed']:
            repos[repo]['passed'] += 1
            total_passed += 1
        else:
            repos[repo]['failed'] += 1
            
    total_failed = total_tests - total_passed
    
    commit, branch = get_git_info()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    # 1. Meta Grid (Overall Status)
    meta_html = f"""
    <div class="meta-grid">
        <div class="meta-card">
            <div class="meta-label">Build Context</div>
            <div><strong>Commit:</strong> {commit}</div>
            <div><strong>Branch:</strong> {branch}</div>
            <div><strong>Time:</strong> {timestamp}</div>
        </div>
        <div class="meta-card">
            <div class="meta-label">Overall Status</div>
            <div style="font-size: 1.5rem; margin-bottom: 5px;">
                <span style="color: var(--pass);">✓ {total_passed} Passed</span><br>
                <span style="color: {'var(--fail)' if total_failed > 0 else 'inherit'};">✗ {total_failed} Failed</span>
            </div>
        </div>
        <div class="meta-card">
            <div class="meta-label">Metrics</div>
            <div><strong>Duration:</strong> {total_duration:.1f} s</div>
            <div><strong>Warnings:</strong> {total_warnings}</div>
            <div><strong>Repositories:</strong> {len(repos)}</div>
        </div>
    </div>
    """
    
    # 2. Repo Summary Table
    repo_table_rows = ""
    for repo, data in repos.items():
        status_icon = "✅" if data['failed'] == 0 else "❌"
        repo_table_rows += f"""
        <tr>
            <td><strong>{repo}</strong></td>
            <td style="text-align: right;">{data['tests']}</td>
            <td style="text-align: right;">{data['passed']}</td>
            <td style="text-align: right; color: {'var(--fail)' if data['failed'] > 0 else 'inherit'};">{data['failed']}</td>
            <td style="text-align: right;">{data['duration']:.1f}s</td>
            <td style="text-align: center;">{status_icon}</td>
        </tr>
        """
        
    repo_table_html = f"""
    <h2>Repository Summary</h2>
    <table>
        <thead>
            <tr>
                <th>Repository</th>
                <th style="text-align: right;">Tests</th>
                <th style="text-align: right;">Passed</th>
                <th style="text-align: right;">Failed</th>
                <th style="text-align: right;">Time</th>
                <th style="text-align: center;">Status</th>
            </tr>
        </thead>
        <tbody>
            {repo_table_rows}
        </tbody>
    </table>
    """
    
    # 3. Repository Cards
    repo_cards_html = '<div class="repo-cards">'
    for repo, data in repos.items():
        status_class = "pass" if data['failed'] == 0 else "fail"
        repo_cards_html += f"""
        <div class="repo-card {status_class}">
            <div class="repo-card-title">{repo}</div>
            <div class="repo-stats">
                <div class="stat-box">
                    <div class="stat-num" style="color: var(--pass);">{data['passed']}</div>
                    <div style="font-size: 0.8rem; color: #666;">PASS</div>
                </div>
                <div class="stat-box">
                    <div class="stat-num" style="color: {'var(--fail)' if data['failed'] > 0 else '#666'};">{data['failed']}</div>
                    <div style="font-size: 0.8rem; color: #666;">FAIL</div>
                </div>
                <div class="stat-box">
                    <div class="stat-num" style="color: #333;">{data['duration']:.1f}s</div>
                    <div style="font-size: 0.8rem; color: #666;">TIME</div>
                </div>
                <div class="stat-box">
                    <div class="stat-num" style="color: #333;">{data['warnings']}</div>
                    <div style="font-size: 0.8rem; color: #666;">WARN</div>
                </div>
            </div>
        </div>
        """
    repo_cards_html += '</div>'
    
    # 4. Detailed Target Results
    details_html = "<h2>Test Details</h2><table><thead><tr><th>Repository</th><th>Target</th><th>Status</th><th>Duration</th><th>Artifacts</th></tr></thead><tbody>"
    
    for idx, run in enumerate(runs):
        repo = run['config_name']
        target = run['target_name']
        passed = run['passed']
        
        status_badge = '<span class="status-badge badge-pass">PASS</span>' if passed else '<span class="status-badge badge-fail">FAIL</span>'
        row_class = "expandable" if not passed else ""
        onclick = f"onclick=\"toggleDetails('details-{idx}')\"" if not passed else ""
        
        # Artifact links
        log_link = f'<a href="../{run["log_path"]}" target="_blank">📄 log</a>'
        artifacts_html = f"<div class='artifact-links'>{log_link}</div>"
        
        details_html += f"""
        <tr class="{row_class}" {onclick}>
            <td>{repo}</td>
            <td><strong>{target}</strong></td>
            <td>{status_badge}</td>
            <td>{run['duration_s']:.2f}s</td>
            <td>{artifacts_html}</td>
        </tr>
        """
        
        if not passed:
            error_text = "\\n".join(run.get('errors', []))
            if not error_text:
                error_text = "Test execution failed or parsing regex detected an error.\\nCheck the full log for details."
                
            details_html += f"""
            <tr id="details-{idx}" class="details-row">
                <td colspan="5" style="padding: 0;">
                    <div class="details-content">
                        <div style="font-weight: 600; margin-bottom: 8px; color: var(--fail);">Failure Details:</div>
                        <pre>{error_text}</pre>
                        <div style="margin-top: 10px;"><a href="../{run['log_path']}" target="_blank" style="color: #2563eb; font-size: 0.9rem;">View Full Log →</a></div>
                    </div>
                </td>
            </tr>
            """
            
    details_html += "</tbody></table>"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EDA Regression Dashboard</title>
        <style>
            :root {{ --primary: #0f172a; --bg: #f8fafc; --card-bg: #ffffff; --text: #334155; --border: #e2e8f0; --pass: #10b981; --fail: #ef4444; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background-color: var(--bg); color: var(--text); padding: 40px 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ color: var(--primary); font-size: 2.2rem; margin-bottom: 20px; border-bottom: 2px solid var(--border); padding-bottom: 15px; }}
            h2 {{ color: var(--primary); font-size: 1.5rem; margin-top: 40px; margin-bottom: 15px; }}
            
            .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .meta-card {{ background: var(--card-bg); padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid var(--border); line-height: 1.6; }}
            .meta-label {{ font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; font-weight: 600; }}
            
            .repo-cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .repo-card {{ background: var(--card-bg); border-radius: 8px; padding: 20px; border-left: 5px solid var(--primary); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .repo-card.pass {{ border-left-color: var(--pass); }}
            .repo-card.fail {{ border-left-color: var(--fail); }}
            .repo-card-title {{ font-size: 1.2rem; font-weight: 600; margin-bottom: 20px; color: var(--primary); }}
            .repo-stats {{ display: flex; justify-content: space-between; }}
            .stat-box {{ text-align: center; }}
            .stat-num {{ font-size: 1.4rem; font-weight: bold; margin-bottom: 4px; }}
            
            table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; margin-bottom: 40px; }}
            th, td {{ padding: 14px 20px; text-align: left; border-bottom: 1px solid var(--border); }}
            th {{ background-color: #f1f5f9; font-weight: 600; color: #475569; }}
            tr:last-child td {{ border-bottom: none; }}
            .status-badge {{ padding: 4px 12px; border-radius: 999px; font-size: 0.85rem; font-weight: bold; display: inline-block; }}
            .badge-pass {{ background-color: #d1fae5; color: #065f46; }}
            .badge-fail {{ background-color: #fee2e2; color: #991b1b; }}
            
            .expandable {{ cursor: pointer; transition: background-color 0.15s; }}
            .expandable:hover {{ background-color: #f8fafc; }}
            .details-row {{ display: none; background-color: #f8fafc; }}
            .details-content {{ padding: 15px 20px; border-left: 4px solid var(--fail); margin: 0; background: #fff; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }}
            pre {{ margin: 0; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.9rem; color: #334155; background: #f1f5f9; padding: 12px; border-radius: 6px; overflow-x: auto; }}
            
            .artifact-links a {{ color: #2563eb; text-decoration: none; font-size: 0.95rem; font-weight: 500; }}
            .artifact-links a:hover {{ text-decoration: underline; }}
        </style>
        <script>
            function toggleDetails(id) {{
                const el = document.getElementById(id);
                if (el.style.display === 'table-row') {{
                    el.style.display = 'none';
                }} else {{
                    el.style.display = 'table-row';
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>EDA Regression Dashboard</h1>
            
            {meta_html}
            {repo_table_html}
            
            <h2>Repository Health</h2>
            {repo_cards_html}
            
            {details_html}
        </div>
    </body>
    </html>
    """
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)
        
    print(f"HTML report generated at {output_path}")
    return True
