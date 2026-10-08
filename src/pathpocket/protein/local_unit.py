"""Five-copy PDB export with repeat-aware identity and strictly rigid normalization."""
from dataclasses import dataclass,asdict
from pathlib import Path
import json
import numpy as np
from .aggregate import detect,AggregateError,RepeatResidueID,window_ca
from .repeat_geometry import RepeatPolicy,rigid_rmsd
from .normalization import csv_table
from .structure import atoms,fit
from pathpocket.core.provenance import sha256

@dataclass
class LocalRepeatUnit:
    rawframe:str
    aligned:str
    manifest:dict

def intrinsic_frame(ca):
    ca=np.asarray(ca);origin=ca.mean(0);e1=ca[1]-ca[0];e1=e1/np.linalg.norm(e1)
    for point in ca[2:]:
        e2=point-ca[0];e2-=np.dot(e2,e1)*e1
        if np.linalg.norm(e2)>1e-6:break
    if np.linalg.norm(e2)<=1e-6:raise ValueError('No intrinsic backbone frame')
    e2/=np.linalg.norm(e2);e3=np.cross(e1,e2);return np.column_stack([e1,e2,e3]),origin

def adapt(path,out,reference=None,policy=RepeatPolicy()):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);d=detect(path,policy);summary=d.summary();manifest=dict(status=d.status,source=str(path),source_sha256=sha256(path),prepared_chains=[],residue_mapping=[],coordinate_changes='none; aligned output only uses one rigid transform',warnings=d.warnings)
    complete=False
    try:
        if d.status!='REPEAT_AGGREGATE_PASS':raise AggregateError(d)
        selected=d.selected_chains.copy();orientation=dict(status='SINGLE_STRUCTURE_CONVENTION',axis_sign=d.geometry.axis_sign_convention)
        if reference:
            ref=atoms(reference);refca={a['residue']:a['xyz'] for a in ref if a['atom']=='CA'};scores=[]
            for trial in [selected,selected[::-1]]:
                mobile=[];fixed=[]
                for label,chain in zip('ABCDE',trial):
                    for pos,xyz in sorted(d.ca[chain].items()):
                        key=f'{label}:{pos}:_'
                        if key in refca:mobile.append(xyz);fixed.append(refca[key])
                scores.append(rigid_rmsd(mobile,fixed))
            choice=int(scores[1]<scores[0]-policy.orientation_equivalence_rmsd_A);selected=selected[::-1] if choice else selected
            orientation=dict(status='AXIS_ORIENTATION_EQUIVALENT' if abs(scores[0]-scores[1])<=policy.orientation_equivalence_rmsd_A else 'REFERENCE_GEOMETRY_ORIENTATION',forward_rmsd_A=scores[0],reverse_rmsd_A=scores[1],reversed=bool(choice),biological_direction=False)
        rotation,origin=intrinsic_frame(list(d.ca[d.central_chain].values()));rawlines=[];aligned=[];mapping=[];serial=0
        for offset,label,chain in zip(range(-2,3),'ABCDE',selected):
            manifest['prepared_chains'].append(dict(prepared_chain_id=label,repeat_offset=offset,original_chain_id=chain,repeat_class='RC_001'))
            for a in sorted(d.chains[chain],key=lambda a:(d.residue_positions[chain][a['residue']],a['atom'])):
                pos=d.residue_positions[chain][a['residue']];serial+=1;prefix=f'ATOM  {serial:5d} {a["atom"]:>4s} {a["resname"].strip():3s} {label}{pos:4d}    '
                occ=a.get('occupancy',float(a['line'][54:60] or 1) if a.get('line') else 1);bf=a.get('bfactor',float(a['line'][60:66] or 0) if a.get('line') else 0);suffix=f'{occ:6.2f}{bf:6.2f}          {a["element"]:>2s}  '
                rawlines.append(prefix+''.join(f'{v:8.3f}' for v in a['xyz'])+suffix);aligned.append(prefix+''.join(f'{v:8.3f}' for v in ((a['xyz']-origin)@rotation))+suffix)
            for raw,pos in d.residue_positions[chain].items():mapping.append(dict(original_chain=chain,original_residue_id=raw,prepared_residue_id=f'{label}:{pos}:_',canonical_repeat_id=RepeatResidueID('RC_001',offset,pos).serialize()))
        for name,lines in [('local_unit_rawframe.pdb',rawlines),('local_unit_aligned.pdb',aligned)]:
            (out/name).write_text('\n'.join(lines)+'\nEND\n');atoms(out/name)
        manifest.update(residue_mapping=mapping,orientation=orientation,normalization_rotation=rotation.tolist(),normalization_origin=origin.tolist(),rawframe_sha256=sha256(out/'local_unit_rawframe.pdb'),aligned_sha256=sha256(out/'local_unit_aligned.pdb'),central_original_chain=d.central_chain,selected_atom_count=serial,pdb_coordinate_rounding_max_A=.0005,window_radius=2)
        summary['orientation']=orientation;summary['prepared_chains']=manifest['prepared_chains'];csv_table(out/'repeat_residue_mapping.csv',mapping,list(mapping[0]));complete=True;return LocalRepeatUnit(str(out/'local_unit_rawframe.pdb'),str(out/'local_unit_aligned.pdb'),manifest)
    finally:
        (out/'README.md').write_text('# Restricted repeat aggregate adapter\nOriginal coordinates retained in rawframe. Comparison normalization is rigid only. See QC and identity manifest.\n')
        summary['export_status']='COMPLETE' if complete else 'NOT_EXPORTED'
        for name,value in [('aggregate_detection_summary.json',summary),('local_unit_manifest.json',manifest),('aggregate_qc.json',dict(status=d.status,passed=complete,policy=asdict(policy),warnings=d.warnings,scope='single repeat-equivalence class, single stack; no pocket science'))]:
            (out/name).write_text(json.dumps(value,indent=2))
        rows=[asdict(c) for c in d.copies] or d.details.get('candidate_chains',[])
        if manifest.get('orientation',{}).get('reversed'):
            for row in rows:row['repeat_offset']=-row['repeat_offset']
        csv_table(out/'repeat_chain_table.csv',rows,list(rows[0]) if rows else ['original_chain_id','repeat_class_id','repeat_offset','status'])
        geometry=[asdict(d.geometry)] if d.geometry else [];csv_table(out/'repeat_geometry.csv',geometry,list(geometry[0]) if geometry else ['axis','explained_variance','spacing_cv','status'])
