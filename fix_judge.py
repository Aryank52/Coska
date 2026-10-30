with open('frontend/src/pages/JudgeMode.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the JUDGE_STEPS - replace emoji icons with string identifiers
content = content.replace(
    """const JUDGE_STEPS = [
  { key: 'incident', label: 'Incident', icon: 'incident' },
  { key: 'evidence', label: 'Evidence', icon: 'evidence' },
  { key: 'hypotheses', label: 'Hypotheses', icon: 'hypotheses' },
  { key: 'root-cause', label: 'Root Cause', icon: 'root-cause' },
  { key: 'remediation', label: 'Remediation', icon: 'remediation' },
  { key: 'verification', label: 'Verification', icon: 'verification' },
]""",
"""const JUDGE_STEPS = [
  { key: 'incident', label: 'Incident', icon: 'incident' },
  { key: 'evidence', label: 'Evidence', icon: 'evidence' },
  { key: 'hypotheses', label: 'Hypotheses', icon: 'hypotheses' },
  { key: 'root-cause', label: 'Root Cause', icon: 'root-cause' },
  { key: 'remediation', label: 'Remediation', icon: 'remediation' },
  { key: 'verification', label: 'Verification', icon: 'verification' },
];""")

with open('frontend/src/pages/JudgeMode.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed JUDGE_STEPS')