"""Backward-compatible structural routing; repeat QC never relaxes homomer matching."""
from pathlib import Path
import json
from .aggregate import AggregateError,is_repeat_candidate,RepeatResidueID
from .aggregate_io import read_polymer
from .local_unit import adapt
from .normalization import normalize,csv_table
from .structure import atoms

def prepare_and_normalize(receptors,out,mode='auto'):
    out=Path(out);adapters=[];reference=None
    try:
        for r in receptors:
            candidate=False
            if mode!='conventional':candidate=is_repeat_candidate(read_polymer(r['path']))
            if mode=='repeat_aggregate' or candidate:
                dest=out/'aggregate'/r['receptor_id'];dest.parent.mkdir(exist_ok=True)
                unit=adapt(r['path'],dest,reference=reference);reference=reference or unit.rawframe;r.update(raw_path=r['path'],path=unit.rawframe,structure_mode='repeat_aggregate')
                summary=json.loads((dest/'aggregate_detection_summary.json').read_text());summary.update(receptor_id=r['receptor_id'],state_id=r['state_id']);adapters.append(summary)
            else:r['structure_mode']='conventional'
        modes={r['structure_mode'] for r in receptors}
        if len(modes)>1:raise ValueError('Mixed conventional/repeat structures are outside this adapter scope; no monomer-versus-aggregate comparison')
        maps,mapping=normalize(receptors,out)
        if modes=={'repeat_aggregate'}:
            for rid,lookup in maps.items():
                for raw,canonical in list(lookup.items()):
                    chain,pos,_=canonical.split(':');offset=int(chain.split('_')[1])-3;lookup[raw]=RepeatResidueID('RC_001',offset,int(pos)).serialize()
            (out/'residue_identity_maps.json').write_text(json.dumps(maps,indent=2));mapping['mapping_mode']='repeat_equivalence';mapping['canonical_identity']='repeat_class:repeat_offset:canonical_position'
            import csv
            rows=list(csv.DictReader((out/'residue_mapping.csv').open()))
            for row in rows:
                chain,pos,_=row['canonical_residue_id'].split(':');row['canonical_residue_id']=RepeatResidueID('RC_001',int(chain.split('_')[1])-3,int(pos)).serialize()
            csv_table(out/'residue_mapping.csv',rows,list(rows[0]));(out/'mapping_summary.json').write_text(json.dumps(mapping,indent=2))
        summary=dict(structure_mode=next(iter(modes)),status='REPEAT_AGGREGATE_PASS' if adapters else 'NOT_AGGREGATE',adapters=adapters)
        for r in receptors:
            records=atoms(r['path']);r.update(heavy_atoms=len(records),residues=len({a['residue'] for a in records}))
        return maps,mapping,summary
    except AggregateError as exc:
        if mode=='auto' and exc.detection.status=='INSUFFICIENT_REPEAT_COPIES':
            exc.detection.details['repeat_geometry_rejection']='INSUFFICIENT_REPEAT_COPIES';exc.detection.status='AMBIGUOUS_HOMOMER'
        summary=dict(structure_mode='unsupported_aggregate',status=exc.detection.status,reason=str(exc),adapters=adapters+[exc.detection.summary()]);raise
    finally:
        if 'summary' in locals():(out/'aggregate_detection_summary.json').write_text(json.dumps(summary,indent=2))
