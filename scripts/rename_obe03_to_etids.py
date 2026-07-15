#!/usr/bin/env python3
"""One-time helper to rename OBE03 labels to ETIDS in a project checkout.
Run from the project root. Review with git diff before committing.
"""
from pathlib import Path
SKIP_DIRS = {'.git', 'node_modules', '.next', '__pycache__', 'logs', 'volumes'}
SKIP_SUFFIXES = {'.zip', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.docx', '.pptx'}

def is_text(path: Path) -> bool:
    try:
        path.read_bytes().decode('utf-8')
        return True
    except Exception:
        return False

root = Path.cwd()
for p in sorted(root.rglob('*'), key=lambda x: len(str(x)), reverse=True):
    if any(part in SKIP_DIRS for part in p.parts):
        continue
    newname = p.name.replace('OBE03','ETIDS').replace('Obe03','ETIDS').replace('obe03','etids')
    if newname != p.name:
        p.rename(p.with_name(newname))

for f in root.rglob('*'):
    if not f.is_file() or any(part in SKIP_DIRS for part in f.parts) or f.suffix.lower() in SKIP_SUFFIXES:
        continue
    if is_text(f):
        s = f.read_text(encoding='utf-8')
        s = s.replace('OBE03','ETIDS').replace('Obe03','ETIDS').replace('obe03','etids')
        f.write_text(s, encoding='utf-8')
print('Completed OBE03 → ETIDS text and filename replacement. Review with git diff.')
