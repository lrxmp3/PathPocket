"""Local residue identity normalization. Never creates or modifies coordinates."""
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

AA = dict(zip('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL'.split(), 'ARNDCQEGHILKMFPSTWYV'))

class MappingStatus(str, Enum):
    PASS='PASS'
    PASS_WITH_GAPS='PASS_WITH_GAPS'
    AMBIGUOUS='AMBIGUOUS'
    LOW_CONFIDENCE='LOW_CONFIDENCE'
    UNSUPPORTED_RESIDUE='UNSUPPORTED_RESIDUE'

class MappingError(ValueError):
    def __init__(self,status,message,details=None):
        self.status=MappingStatus(status);self.details=details or []
        super().__init__(self.status.value+': '+message)

@dataclass(frozen=True)
class RawResidueID:
    chain_id:str
    residue_number:int
    insertion_code:str=''
    def serialize(self):return f'{self.chain_id or "_"}:{self.residue_number}:{self.insertion_code or "_"}'
    @classmethod
    def parse(cls,key):
        c,n,i=key.split(':');return cls('' if c=='_' else c,int(n),'' if i=='_' else i)

@dataclass(frozen=True)
class CanonicalResidueID:
    canonical_chain_id:str
    canonical_position:int
    reference_residue_name:str
    def serialize(self):return f'{self.canonical_chain_id}:{self.canonical_position:06d}:{self.reference_residue_name}'
    @classmethod
    def parse(cls,key):
        c,p,n=key.split(':');return cls(c,int(p),n)

@dataclass(frozen=True)
class MappingConfidence:
    identity:float
    coverage_ref:float
    coverage_target:float
    gap_count:int
    mismatch_count:int
    @property
    def score(self):return self.identity*min(self.coverage_ref,self.coverage_target)

@dataclass
class ResidueMapping:
    target_to_reference:dict
    insertions:dict
    confidence:MappingConfidence
    mode:str
    alignment_ambiguous:bool=False

@dataclass(frozen=True)
class MappingPolicy:
    min_chain_identity:float=.95
    min_chain_coverage:float=.90
    ambiguity_margin:float=.02
    on_ambiguous:str='fail'

def extract_chains(records):
    """Observed ATOM order, including insertion codes; missing residues stay absent."""
    chains={};seen={}
    for atom in records:
        raw=RawResidueID.parse(atom['residue']);name=atom['resname'].strip()
        if name not in AA:raise MappingError('UNSUPPORTED_RESIDUE',f'{raw.serialize()} has nonstandard ATOM residue {name}')
        key=raw.serialize()
        if key in seen:
            if seen[key]!=name:raise MappingError('LOW_CONFIDENCE','Conflicting residue names for '+key)
            continue
        seen[key]=name
        chains.setdefault(raw.chain_id,[]).append(dict(raw_id=key,resname=name,aa=AA[name]))
    return chains

def _confidence(ref,target,pairs):
    matches=sum(ref[i]['aa']==target[j]['aa'] for j,i in pairs.items());n=len(pairs)
    return MappingConfidence(matches/n if n else 0,n/len(ref),n/len(target),len(ref)+len(target)-2*n,n-matches)

def identity_mapping(ref,target,policy=MappingPolicy()):
    lookup={r['raw_id']:i for i,r in enumerate(ref)}
    pairs={j:lookup[r['raw_id']] for j,r in enumerate(target) if r['raw_id'] in lookup}
    c=_confidence(ref,target,pairs)
    if c.mismatch_count or min(c.coverage_ref,c.coverage_target)<policy.min_chain_coverage:return None
    if list(pairs.values())!=sorted(pairs.values()):return None
    inserts={};anchor=0
    for j in range(len(target)):
        if j in pairs:anchor=pairs[j]+1
        else:inserts.setdefault(anchor,[]).append(j)
    return ResidueMapping(pairs,inserts,c,'identity')

def sequence_mapping(ref,target):
    """Deterministic global affine-gap alignment; tied residue maps are flagged."""
    from Bio.Align import PairwiseAligner
    aligner=PairwiseAligner(mode='global',match_score=2,mismatch_score=-1,open_gap_score=-4,extend_gap_score=-.5)
    alignments=aligner.align(''.join(x['aa'] for x in ref),''.join(x['aa'] for x in target))
    first=alignments[0];indices=first.indices
    try:ambiguous=not np.array_equal(indices,alignments[1].indices)
    except IndexError:ambiguous=False
    pairs={};inserts={};anchor=0
    for i,j in indices.T:
        if i>=0:anchor=int(i)+1
        if i>=0 and j>=0:pairs[int(j)]=int(i)
        elif j>=0:inserts.setdefault(anchor,[]).append(int(j))
    return ResidueMapping(pairs,inserts,_confidence(ref,target,pairs),'sequence',ambiguous)

def qualified(mapping,policy=MappingPolicy()):
    c=mapping.confidence
    return c.identity>=policy.min_chain_identity and min(c.coverage_ref,c.coverage_target)>=policy.min_chain_coverage
