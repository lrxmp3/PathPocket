"""One-to-one chain correspondence with explicit confidence and ambiguity gates."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import linear_sum_assignment
from .residue_mapping import MappingPolicy,MappingError,identity_mapping,sequence_mapping,qualified

@dataclass
class ChainMapping:
    reference_chain:str
    target_chain:str
    residue_mapping:object
    status:str
    ambiguity:bool=False

def assign_chains(reference,target,policy=MappingPolicy(),reference_self=False):
    if len(reference)!=len(target):raise MappingError('LOW_CONFIDENCE','Different chain counts; partial assembly correspondence is not supported')
    # Existing identifiers are an explicit compatibility contract, not inferred homomer symmetry.
    identity=[]
    if set(reference)==set(target):
        for c in reference:
            m=identity_mapping(reference[c],target[c],policy)
            if m is None:break
            identity.append(ChainMapping(c,c,m,'PASS_WITH_GAPS' if m.confidence.gap_count else 'PASS'))
        if len(identity)==len(reference):return identity
    refs=list(reference);targets=list(target);matrix=np.full((len(refs),len(targets)),-1e6);pairs={};details=[]
    for i,r in enumerate(refs):
        for j,t in enumerate(targets):
            m=sequence_mapping(reference[r],target[t]);pairs[i,j]=m
            details.append(dict(reference_chain=r,target_chain=t,**m.confidence.__dict__,score=m.confidence.score,alignment_ambiguous=m.alignment_ambiguous))
            if qualified(m,policy):matrix[i,j]=m.confidence.score
    rows,cols=linear_sum_assignment(-matrix)
    if any(matrix[i,j]<0 for i,j in zip(rows,cols)):raise MappingError('LOW_CONFIDENCE','No full chain assignment meets identity and both coverage thresholds',details)
    best=float(matrix[rows,cols].sum())
    for i,j in zip(rows,cols):
        alternative=matrix.copy();alternative[i,j]=-1e6;a,b=linear_sum_assignment(-alternative)
        if all(alternative[x,y]>=0 for x,y in zip(a,b)) and (best-float(alternative[a,b].sum()))/len(refs)<=policy.ambiguity_margin:
            raise MappingError('AMBIGUOUS','Multiple sequence-equivalent chain assignments; geometry/symmetry disambiguation is not implemented',details)
        if pairs[i,j].alignment_ambiguous:raise MappingError('AMBIGUOUS','Global sequence alignment has multiple optimal residue correspondences',details)
    return [ChainMapping(refs[i],targets[j],pairs[i,j],'PASS_WITH_GAPS' if pairs[i,j].confidence.gap_count else 'PASS') for i,j in zip(rows,cols)]
