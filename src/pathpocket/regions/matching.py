"""Deterministic complete-link matching in a shared protein frame."""
import itertools
import numpy as np

def jaccard(a,b):
    a,b=set(a),set(b);return len(a&b)/len(a|b) if a|b else 0.0

def clusters(instances,cutoff,overlap):
    groups=[]
    for item in sorted(instances,key=lambda r:r['region_instance_id']):
        eligible=[g for g in groups if all(np.linalg.norm(np.array(item['center'])-x['center'])<=cutoff and jaccard(item['residues'],x['residues'])>=overlap for x in g)]
        if eligible:
            group=min(eligible,key=lambda g:np.mean([np.linalg.norm(np.array(item['center'])-x['center']) for x in g]));group.append(item)
        else:groups.append([item])
    return groups

def match_regions(instances,receptors,cutoff=6.0,overlap=.3,sensitivity=False):
    base=clusters(instances,cutoff,overlap);states=list(dict.fromkeys(r['state_id'] for r in receptors));result=[]
    trials=[clusters(instances,cutoff*c,min(1,max(0,overlap+j))) for c,j in itertools.product([.8,1,1.2],[-.1,0,.1])] if sensitivity else []
    for i,g in enumerate(base,1):
        ids={x['region_instance_id'] for x in g};residues=sorted(set().union(*(set(x['residues']) for x in g)))
        receptor_ids={x['receptor_id'] for x in g}
        consensus=[r for r in residues if len({x['receptor_id'] for x in g if r in x['residues']})/len(receptor_ids)>=.5]
        occ={s:len({x['receptor_id'] for x in g if x['state_id']==s})/sum(r['state_id']==s for r in receptors) for s in states}
        stability=float(np.median([max(jaccard(ids,{x['region_instance_id'] for x in candidate}) for candidate in groups) for groups in trials])) if trials else None
        result.append(dict(region_family_id=f'RF_{i:04d}',members=sorted(ids),consensus_residues=consensus,center=np.mean([x['center'] for x in g],axis=0).tolist(),state_occurrence=occ,matching_stability=stability,matching_stability_evaluated=bool(trials)))
    return result
