#!/usr/bin/env python3
"""Native Linux equivalent of the small bootstrap context checks."""
from pathlib import Path
import argparse
import re
import subprocess

def check(root, require_remote=False):
    required = ['AGENTS.md','README.md','.gitignore','.gitattributes',
        *['for-ai/'+name+'.md' for name in ['README','PROJECT','SKILLS','VERIFICATION','WORKFLOW','DECISIONS']],
        'for-ai/scripts/check-context.ps1']
    for name in required:
        assert (root/name).is_file(), name
    assert 'for-ai/README.md' in (root/'AGENTS.md').read_text()
    for path in (root/'for-ai').rglob('*.md'):
        assert not re.search(r'\{\{[A-Z0-9_]+\}\}',path.read_text()),path
        assert len(path.read_text().splitlines()) <= 500,path
    tracked = subprocess.check_output(['git','ls-files'],cwd=root,text=True).splitlines()
    for name in tracked:
        assert not re.search(r'(^|/)(\.env($|\.)|id_rsa|id_ed25519|.*\.(pem|p12|pfx)$)',name),name
        if name.startswith('for-ai/'):
            assert Path(name).suffix.lower() not in ['.png','.jpg','.wav','.zip','.pdf'],name
    if require_remote:
        branch = subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()
        head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        remote = subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=root,text=True).split()[0]
        assert head==remote,(head,remote)
    print('Context check: VERIFIED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--require-remote',action='store_true')
    args=parser.parse_args();check(Path(__file__).resolve().parents[2],args.require_remote)
