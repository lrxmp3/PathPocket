"""Restricted repeat-equivalence detection. Ordinary homomer safety gates remain intact."""
from dataclasses import dataclass,field,asdict
from enum import Enum
import numpy as np
from .aggregate_io import read_polymer,residues
from .repeat_geometry import RepeatPolicy,RepeatGeometry,axis_geometry,rigid_rmsd,contact_count
from .residue_mapping import sequence_mapping

class AggregateMappingStatus(str,Enum):
    NOT_AGGREGATE='NOT_AGGREGATE'
    REPEAT_AGGREGATE_PASS='REPEAT_AGGREGATE_PASS'
    INSUFFICIENT_REPEAT_COPIES='INSUFFICIENT_REPEAT_COPIES'
    HETERO_AGGREGATE_UNSUPPORTED='HETERO_AGGREGATE_UNSUPPORTED'
    IRREGULAR_REPEAT_SPACING='IRREGULAR_REPEAT_SPACING'
    STRUCTURALLY_IRREGULAR_REPEAT='STRUCTURALLY_IRREGULAR_REPEAT'
    NO_REPEAT_CONTACT='NO_REPEAT_CONTACT'
    NO_VALID_CENTRAL_WINDOW='NO_VALID_CENTRAL_WINDOW'
    CENTRAL_WINDOW_AMBIGUOUS='CENTRAL_WINDOW_AMBIGUOUS'
    MULTI_PROTOFILAMENT_UNSUPPORTED='MULTI_PROTOFILAMENT_UNSUPPORTED'
    AMBIGUOUS_HOMOMER='AMBIGUOUS_HOMOMER'

@dataclass(frozen=True)
class RepeatResidueID:
    repeat_class:str
    repeat_offset:int
    canonical_position:int
    def serialize(self):return f'{self.repeat_class}:{self.repeat_offset:+d}:{self.canonical_position}'.replace(':+0:',':0:')
    @classmethod
    def parse(cls,text):c,o,p=text.split(':');return cls(c,int(o),int(p))

@dataclass
class RepeatCopy:
    original_chain_id:str
    repeat_class_id:str
    repeat_offset:int
    axial_coordinate:float
    sequence_identity:float
    coverage_ref:float
    coverage_target:float
    chain_rmsd:float
    is_terminal:bool
    left_neighbor_count:int
    right_neighbor_count:int
    usable_as_center:bool
    centroid:list
    ca_count:int
    sequence_length:int
    contacts_to_next:int

@dataclass
class RepeatEquivalenceClass:
    repeat_class_id:str
    sequence:str
    copies:list

@dataclass
class AggregateDetection:
    status:str
    policy:dict
    copy_count:int
    repeat_class_count:int=0
    geometry:object=None
    copies:list=field(default_factory=list)
    central_chain:str|None=None
    selected_chains:list=field(default_factory=list)
    warnings:list=field(default_factory=list)
    details:dict=field(default_factory=dict)
    chains:dict=field(default_factory=dict,repr=False)
    residue_positions:dict=field(default_factory=dict,repr=False)
    ca:dict=field(default_factory=dict,repr=False)
    def summary(self):
        return dict(structure_mode='repeat_aggregate' if self.status=='REPEAT_AGGREGATE_PASS' else 'unsupported_aggregate',status=self.status,repeat_class_count=self.repeat_class_count,copy_count=self.copy_count,central_original_chain=self.central_chain,window_radius=self.policy['repeat_radius'],repeat_offsets=list(range(-self.policy['repeat_radius'],self.policy['repeat_radius']+1)) if self.selected_chains else [],selected_original_chains=self.selected_chains,policy=self.policy,geometry=asdict(self.geometry) if self.geometry else None,warnings=self.warnings,**self.details)

class AggregateError(ValueError):
    def __init__(self,detection):self.detection=detection;super().__init__('Structure adaptation stopped safely: '+detection.status)

def is_repeat_candidate(chains):
    sequences=[''.join(r['aa'] for r in residues(a)) for a in chains.values()]
    if len(sequences)<2:return False
    for i,a in enumerate(sequences):
        for b in sequences[i+1:]:
            if a==b:return True
            # Gate routing only; full coverage/identity certification is done by detect.
            from .aggregate_io import AA
            inverse={v:k for k,v in AA.items()};ra=[dict(aa=x,resname=inverse[x]) for x in a];rb=[dict(aa=x,resname=inverse[x]) for x in b];m=sequence_mapping(ra,rb).confidence
            if m.identity>=.95 and min(m.coverage_ref,m.coverage_target)>=.90:return True
    return False

def window_ca(ca,chains):
    common=sorted(set.intersection(*(set(ca[c]) for c in chains)))
    if len(common)<3:raise ValueError('Insufficient shared CA positions')
    return np.array([ca[c][p] for c in chains for p in common])

def detect(path,policy=RepeatPolicy()):
    chains=read_polymer(path) if not isinstance(path,dict) else path;names=list(chains);n=len(names);d=AggregateDetection('NOT_AGGREGATE',asdict(policy),n,chains=chains)
    def stop(status,**details):d.status=status;d.details.update(details);return d
    if n<policy.min_repeat_copies:return stop('INSUFFICIENT_REPEAT_COPIES')
    seq={c:residues(chains[c]) for c in names};ref=max(seq,key=lambda c:(len(seq[c]),''.join(x['aa'] for x in seq[c])));conf={}
    for c in names:
        m=sequence_mapping(seq[ref],seq[c]);q=m.confidence
        if q.identity<policy.min_identity or min(q.coverage_ref,q.coverage_target)<policy.min_coverage:return stop('HETERO_AGGREGATE_UNSUPPORTED',failed_chain=c)
        if m.alignment_ambiguous:return stop('AMBIGUOUS_HOMOMER',reason='Non-unique residue sequence alignment')
        if len(m.target_to_reference)!=len(seq[c]):return stop('HETERO_AGGREGATE_UNSUPPORTED',reason='Unmapped insertion positions require a broader adapter')
        conf[c]=q;d.residue_positions[c]={r['raw_id']:m.target_to_reference[j]+1 for j,r in enumerate(seq[c])}
        d.ca[c]={d.residue_positions[c][a['residue']]:a['xyz'] for a in chains[c] if a['atom']=='CA'}
        if len(d.ca[c])<3:return stop('STRUCTURALLY_IRREGULAR_REPEAT',reason='At least three CA atoms required per copy')
    d.repeat_class_count=1
    ca_arrays=[np.array(list(d.ca[c].values())) for c in names];centroids=[x.mean(0) for x in ca_arrays];g=axis_geometry(centroids,ca_arrays,policy);d.geometry=g
    d.details['candidate_chains']=[dict(original_chain_id=c,sequence_length=len(seq[c]),ca_count=len(d.ca[c]),centroid=np.asarray(centroids[i]).tolist(),axial_coordinate=g.projections[i],sequence_identity=conf[c].identity) for i,c in enumerate(names)]
    if g.status!='REPEAT_AGGREGATE_PASS':return stop(g.status)
    ordered=[names[i] for i in g.order];radius=policy.repeat_radius;centers=sorted(set([(n-1)//2,n//2]));centers=[i for i in centers if i>=radius and n-i-1>=radius]
    if not centers:return stop('NO_VALID_CENTRAL_WINDOW')
    if len(centers)==2:
        windows=[ordered[i-radius:i+radius+1] for i in centers]
        try:rmsd=rigid_rmsd(window_ca(d.ca,windows[0]),window_ca(d.ca,windows[1]))
        except ValueError:return stop('CENTRAL_WINDOW_AMBIGUOUS')
        d.details['central_candidate_equivalence_rmsd_A']=rmsd
        if rmsd>policy.central_equivalence_rmsd_A:return stop('CENTRAL_WINDOW_AMBIGUOUS')
        d.warnings.append('CENTRAL_CHOICE_EQUIVALENT: axial-index convention, not biological priority')
    center_index=centers[0];central=ordered[center_index];rmsds={}
    for c in ordered:
        common=sorted(set(d.ca[c])&set(d.ca[central]))
        try:rmsds[c]=rigid_rmsd([d.ca[c][p] for p in common],[d.ca[central][p] for p in common])
        except ValueError:return stop('STRUCTURALLY_IRREGULAR_REPEAT',failed_chain=c)
    d.details.update(median_chain_rmsd_A=float(np.median(list(rmsds.values()))),max_chain_rmsd_A=max(rmsds.values()))
    if max(rmsds.values())>policy.max_repeat_chain_rmsd_A:return stop('STRUCTURALLY_IRREGULAR_REPEAT')
    contacts=[contact_count(list(d.ca[a].values()),list(d.ca[b].values()),policy.contact_cutoff_A) for a,b in zip(ordered,ordered[1:])];d.details['adjacent_CA_contacts']=contacts
    if not all(x>0 for x in contacts):return stop('NO_REPEAT_CONTACT')
    for i,c in enumerate(ordered):
        q=conf[c];index=names.index(c);d.copies.append(RepeatCopy(c,'RC_001',i-center_index,g.projections[index],q.identity,q.coverage_ref,q.coverage_target,rmsds[c],i in [0,n-1],i,n-1-i,i>=radius and n-i-1>=radius,np.asarray(centroids[index]).tolist(),len(d.ca[c]),len(seq[c]),contacts[i] if i<len(contacts) else 0))
    d.central_chain=central;d.selected_chains=ordered[center_index-radius:center_index+radius+1];d.details['repeat_sequence']=''.join(x['aa'] for x in seq[ref]);d.details['sequence_reference_convention']='longest observed sequence, lexical sequence tie; no chain labels'
    if any(c.is_terminal and c.original_chain_id in d.selected_chains for c in d.copies):d.warnings.append('Local outer padding includes a deposited end; central copy is never terminal. Finite-window end effects are not eliminated.')
    d.status='REPEAT_AGGREGATE_PASS';return d
