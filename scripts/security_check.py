#!/usr/bin/env python
"""
COSKA Security Check

Scans for common security issues in the codebase.
"""
import sys
import re
from pathlib import Path
from typing import List, Tuple


SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', "API Key"),
    (r'(?i)(secret|password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{8,})', "Password/Secret"),
    (r'(?i)(token|auth[_-]?token|access[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', "Auth Token"),
    (r'(?i)(private[_-]?key|ssh[_-]?key)\s*[:=]\s*["\']?', "Private Key"),
    (r'(?i)(aws[_-]?access[_-]?key|aws[_-]?secret[_-]?key)', "AWS Credentials"),
    (r'(?i)(database_url|db_url)\s*[:=]\s*["\']?[^"\']*[:/]', "Database URL with credentials"),
]


UNSAFE_COMMANDS = [
    r'\b(rm\s+-rf|del\s+/[sfq]|format\s+[a-z]:)',
    r'\b(curl\s+.*\|\s*sh|wget\s+.*\|\s*sh)',
    r'\b(eval\s*\(|exec\s*\()',
    r'\b(base64\s+-d\s*\|)',
    r'(chmod\s+777|chown\s+root)',
]


SENSITIVE_FILES = [
    r'\.env$',
    r'\.env\.',
    r'id_rsa',
    r'id_dsa',
    r'\.pem$',
    r'\.key$',
    r'\.p12$',
    r'\.pfx$',
    r'\.crt$',
    r'credentials',
    r'secrets',
]


SUSPICIOUS_PATTERNS = [
    (r'\beval\s*\(', "eval() usage"),
    (r'\bexec\s*\(', "exec() usage"),
    (r'\bshell=True', "shell=True in subprocess"),
    (r'subprocess\.call.*shell\s*=\s*True', "subprocess with shell=True"),
    (r'os\.system\s*\(', "os.system() usage"),
    (r'pickle\.loads?\s*\(', "pickle deserialization"),
    (r'yaml\.load\s*\(', "unsafe yaml.load()"),
    (r'xml\.etree.*fromstring', "XML external entity risk"),
    (r'\.format\(.*request\.', "potential format string injection"),
    (r'\.format\(.*\{\{', "template injection risk"),
]


def scan_file(path: Path) -> List[Tuple[str, int, str]]:
    """Scan a single file for security issues."""
    issues = []
    
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # Check for secret patterns
            for pattern, desc in SECRET_PATTERNS:
                if re.search(pattern, line):
                    # Skip if it's in a comment or test file or example
                    if not stripped.startswith('#') and 'test' not in str(path).lower() and '.example' not in str(path).lower():
                        redacted = re.sub(r'([:=]\s*["\']?)[^\s"\']+', r'\1[REDACTED]', stripped)
                        issues.append((f"SECRET: {desc}", line_num, redacted[:100]))
            
            # Check for unsafe commands
            for pattern in UNSAFE_COMMANDS:
                if re.search(pattern, line):
                    issues.append(("UNSAFE_COMMAND", line_num, stripped[:100]))
            
            # Check for suspicious patterns
            for pattern, desc in SUSPICIOUS_PATTERNS:
                if re.search(pattern, line):
                    issues.append((f"SUSPICIOUS: {desc}", line_num, stripped[:100]))
    
    except Exception:
        pass
    
    return issues


def scan_directory(root: Path, exclude_dirs: set = None) -> List[Tuple[str, int, str, Path]]:
    """Recursively scan directory for security issues."""
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.pytest_cache', '.mypy_cache'}
    
    all_issues = []
    import os
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in-place
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.pytest')]
        
        for fname in filenames:
            file_path = Path(dirpath) / fname
            
            # Check for sensitive files
            for pattern in SENSITIVE_FILES:
                if re.search(pattern, fname, re.IGNORECASE):
                    if fname != '.env.example' and not fname.endswith('.example'):
                        try:
                            rel_path = file_path.relative_to(root)
                            all_issues.append(("SENSITIVE_FILE", 0, str(rel_path), file_path))
                        except ValueError:
                            pass
            
            # Check file extension
            if file_path.suffix in {'.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.env', '.sh', '.bash', '.zsh'}:
                issues = scan_file(file_path)
                for issue_type, line_num, snippet in issues:
                    all_issues.append((issue_type, line_num, snippet, file_path))
    
    return all_issues


def check_gitignore(root: Path) -> List[str]:
    """Check .gitignore for proper exclusions."""
    gitignore_path = root / ".gitignore"
    issues = []
    
    if not gitignore_path.exists():
        issues.append(".gitignore not found")
        return issues
    
    content = gitignore_path.read_text()
    required_patterns = [
        '.env',
        '*.key',
        '*.pem',
        '*.p12',
        '*.pfx',
        '*.crt',
        'credentials',
        'secrets',
        '__pycache__',
        'node_modules',
        '.venv',
        'venv',
        'dist',
        'build',
        '.pytest_cache',
    ]
    
    for pattern in required_patterns:
        if pattern not in content:
            issues.append(f".gitignore missing pattern: {pattern}")
    
    return issues


def check_cors_config() -> List[str]:
    """Check CORS configuration."""
    issues = []
    main_py = Path(__file__).parent.parent / "backend" / "app" / "main.py"
    
    if main_py.exists():
        content = main_py.read_text()
        if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
            issues.append("CORS allows all origins (*) - restrict in production")
    
    return issues


def check_secrets_in_git(root: Path) -> List[str]:
    """Check for secrets in git history (basic check)."""
    issues = []
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'log', '--all', '--full-history', '--oneline', '--grep=api_key', '--grep=secret', '--grep=password', '--grep=token', '--grep=apikey'],
            cwd=root, capture_output=True, text=True, timeout=30
        )
        if result.stdout.strip():
            issues.append("Potential secrets found in git history (search for api_key, secret, password, token)")
    except Exception:
        pass
    return issues


def main():
    """Main security check."""
    root = Path(__file__).parent.parent
    
    print("COSKA Security Scan")
    print("=" * 50)
    
    all_issues = []
    
    # Scan source files
    print("\n[1/6] Scanning source files for secrets and unsafe patterns...")
    issues = scan_directory(root)
    if issues:
        print(f"  Found {len(issues)} potential issues:")
        for issue_type, line_num, snippet, file_path in issues[:20]:  # Limit output
            rel_path = file_path.relative_to(Path(__file__).parent.parent)
            print(f"  [{issue_type}] {rel_path}:{line_num} - {snippet}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more issues")
    else:
        print("  No issues found in source files")
    
    # Check .gitignore
    print("\n[2/6] Checking .gitignore...")
    gitignore_issues = check_gitignore(Path(__file__).parent.parent)
    if gitignore_issues:
        for issue in gitignore_issues:
            print(f"  [WARN] {issue}")
    else:
        print("  .gitignore looks good")
    
    # Check CORS
    print("\n[3/6] Checking CORS configuration...")
    cors_issues = check_cors_config()
    if cors_issues:
        for issue in cors_issues:
            print(f"  [WARN] {issue}")
    else:
        print("  CORS configuration looks good")
    
    # Check git history
    print("\n[4/6] Checking git history for secrets...")
    git_issues = check_secrets_in_git(Path(__file__).parent.parent)
    if git_issues:
        for issue in git_issues:
            print(f"  [WARN] {issue}")
    else:
        print("  No obvious secrets in recent git history")
    
    # Check for sensitive files
    print("\n[5/6] Checking for sensitive files...")
    sensitive_issues = [issue for issue in issues if issue[0] == "SENSITIVE_FILE"]
    if sensitive_issues:
        for _, _, rel, _ in sensitive_issues:
            print(f"  [WARN] Sensitive file: {rel}")
    else:
        print("  No sensitive files found in working directory")
    
    # Summary
    print("\n" + "=" * 50)
    print("Security scan complete.")
    print("Review any [WARN] items above.")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())