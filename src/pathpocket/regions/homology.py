from pathlib import Path
import numpy as np
from pathpocket.protein.structure import atoms,ca_map,fit,transform
from pathpocket.core.run_context import write_json

def targets_for_family(family,instances,receptors,out,residue_maps=None):
    def mapped_ca(receptor):
        values=ca_map(atoms(receptor['aligned']))
        return {residue_maps[receptor['receptor_id']][k]:v for k,v in values.items()} if residue_maps else values
    members=[x for x in instances if x['region_instance_id'] in family['members']]
    reference=min(members,key=lambda x:np.linalg.norm(np.array(x['center'])-family['center']))
    byid={r['receptor_id']:r for r in receptors};ref=mapped_ca(byid[reference['receptor_id']])
    center=reference['center'];targets=[]
    for state in family['state_occurrence']:
        detected={x['receptor_id'] for x in members if x['state_id']==state}
        pool=[r for r in receptors if r['state_id']==state and (not detected or r['receptor_id'] in detected)]
        common=set(family['consensus_residues'])&set(ref)
        for r in pool:common &= set(mapped_ca(r))
        common=sorted(common)
        if len(common)<3:raise ValueError('Insufficient local homologous CA anchors for family '+family['region_family_id'])
        arrays=[np.array([mapped_ca(r)[k][1] for k in common]) for r in pool]
        sums=[sum(np.sqrt(((a-b)**2).sum(1).mean()) for b in arrays) for a in arrays]
        chosen=pool[int(np.argmin(sums))];mobile=atoms(chosen['aligned']);ca=mapped_ca(chosen)
        rotation,translation,rmsd=fit([ca[k][1] for k in common],[ref[k][1] for k in common])
        tid=family['region_family_id']+'_'+state;folder=Path(out)/tid;folder.mkdir()
        transform(mobile,rotation,translation,folder/'receptor_full.pdb');transform(mobile,rotation,translation,folder/'receptor.pdb',center)
        write_json(folder/'transform.json',dict(rotation=rotation.tolist(),translation=translation.tolist(),anchors=common,rmsd_A=rmsd,reference_receptor_id=reference['receptor_id']))
        targets.append(dict(target_id=tid,region_family_id=family['region_family_id'],state_id=state,receptor_id=chosen['receptor_id'],receptor=str(folder/'receptor.pdb'),full_receptor=str(folder/'receptor_full.pdb'),center=center,detected_pocket=bool(detected),role=family['role'],local_fit_RMSD_A=rmsd))
    return targets
