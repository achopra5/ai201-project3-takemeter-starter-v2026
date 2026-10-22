"""Versioned evidence checks shared by historical and current validators."""
import hashlib
import json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_file(root, name, original_digest):
    manifest = root / 'submission/unit6_manifest.json'
    transitions = json.loads(manifest.read_text()).get('unit5_evolution', {}) if manifest.exists() else {}
    if set(transitions) - {'label_definitions.txt'}:
        raise ValueError('Unsupported frozen-evidence exception')
    change = transitions.get(name)
    if change:
        if change['historical_sha256'] != original_digest:
            raise ValueError('Historical hash was rewritten')
        if change['original_snapshot'] != 'submission/unit5_originals/label_definitions.txt':
            raise ValueError('Unexpected snapshot path')
        if sha(root / change['original_snapshot']) != original_digest:
            raise ValueError('Historical Unit 5 snapshot changed')
        if sha(root / name) != change['unit6_sha256']:
            raise ValueError('Unit 6 definitions changed after recording')
    elif sha(root / name) != original_digest:
        raise ValueError(f'Frozen input changed: {name}')
