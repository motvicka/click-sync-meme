"""Shared helpers: locate the skill, the project and the clip pack."""
import json, pathlib, sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent

def project(path='.'):
    proj = pathlib.Path(path).resolve()
    pj = proj / 'project.json'
    if not pj.exists():
        sys.exit(f'{pj} not found — run scripts/new_project.py first (or pass --project)')
    return proj, json.loads(pj.read_text())

def clip_pack(clip_id, proj=None):
    """A clip pack lives in the skill (clips/<id>/) or, for your own clips, in the project (clip/)."""
    for d in ([proj / 'clip'] if proj else []) + [SKILL_DIR / 'clips' / clip_id]:
        if (d / 'clip.json').exists():
            return d, json.loads((d / 'clip.json').read_text())
    sys.exit(f'no clip pack "{clip_id}" (looked in the project\'s clip/ and in {SKILL_DIR / "clips"})')

def fps_of(clip):
    n, d = (clip['fps'].split('/') + ['1'])[:2] if isinstance(clip['fps'], str) else (clip['fps'], 1)
    return float(n) / float(d)
