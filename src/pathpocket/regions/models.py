import json
from pathlib import Path
import numpy as np
from pathpocket.core.paths import native_path,safe_id

def load_targets(path,states):
    data=json.loads(Path(path).read_text());targets=data['targets'];seen=set()
    families=data.get('families',[])
    if not families:raise ValueError('Imported manifest requires family summaries')
    family_ids=[safe_id(f['region_family_id']) for f in families]
    if len(set(family_ids))!=len(family_ids):raise ValueError('Duplicate family ID')
    for f in families:
        occurrence=f['state_occurrence']
        if set(occurrence)!=states or any(not np.isfinite(v) or not 0<=v<=1 for v in occurrence.values()):raise ValueError('Invalid family state occurrence')
        stability=f.get('matching_stability')
        if stability is not None and (not np.isfinite(stability) or not 0<=stability<=1):raise ValueError('Invalid matching stability')
        if f.get('strict_state_stable_control') and not (min(occurrence.values())>=.5 and max(occurrence.values())-min(occurrence.values())<=.3 and stability is not None and stability>=.7):raise ValueError('Imported strict control does not satisfy declared thresholds')
    for t in targets:
        for key in ['target_id','region_family_id','state_id']:safe_id(t[key])
        if t['target_id'] in seen:raise ValueError('Duplicate target ID')
        seen.add(t['target_id'])
        if t['state_id'] not in states:raise ValueError('Imported target uses unknown state')
        if t['region_family_id'] not in family_ids:raise ValueError('Unknown target family')
        center=np.asarray(t['center'],dtype=float)
        if center.shape!=(3,) or not np.isfinite(center).all():raise ValueError('Region center must contain 3 finite coordinates')
        if type(t.get('detected_pocket')) is not bool:raise ValueError('detected_pocket must be boolean')
        for key in ['receptor','full_receptor']:
            t[key]=str(native_path(t[key],Path(path).parent))
            if not Path(t[key]).is_file():raise ValueError(f'Imported target file missing: {t[key]}')
    for family in {t['region_family_id'] for t in targets}:
        selected=[t for t in targets if t['region_family_id']==family]
        if {t['state_id'] for t in selected}!=states or len(selected)!=len(states):raise ValueError('Every imported family requires one target per state')
        if not all(np.allclose(t['center'],selected[0]['center']) for t in selected):raise ValueError('Imported family targets must share one local reference center')
    if not targets:raise ValueError('No imported targets')
    return data
