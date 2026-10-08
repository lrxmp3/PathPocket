"""Engineering geometry gates for a single repeat stack. No pocket scores involved."""
from dataclasses import dataclass,asdict
import numpy as np
from .structure import fit

@dataclass(frozen=True)
class RepeatPolicy:
    min_identity:float=.95
    min_coverage:float=.90
    min_repeat_copies:int=5
    min_axis_explained_variance:float=.85
    max_spacing_cv:float=.25
    max_repeat_chain_rmsd_A:float=2.
    contact_cutoff_A:float=8.
    repeat_radius:int=2
    central_equivalence_rmsd_A:float=.10
    orientation_equivalence_rmsd_A:float=.01
    lateral_spacing_ratio:float=.5
    coincident_projection_ratio:float=.25

    def __post_init__(self):
        if self.repeat_radius != 2 or self.min_repeat_copies < 5:
            raise ValueError('R072 supports only a five-copy window and at least five repeats')

@dataclass
class RepeatGeometry:
    axis:list
    explained_variance:float
    order:list
    projections:list
    spacing:list
    spacing_mean:float
    spacing_median:float
    spacing_sd:float
    spacing_cv:float
    status:str
    axis_sign_convention:str

def axis_geometry(centroids,backbones,policy=RepeatPolicy()):
    xyz=np.asarray(centroids);centered=xyz-xyz.mean(0);_,values,vt=np.linalg.svd(centered,full_matrices=False);variance=float(values[0]**2/max(float((values**2).sum()),1e-30));axis=vt[0]
    # Intrinsic sequence-ordered cross products rotate with the molecule. Never use chain labels.
    anchors=[]
    for ca in backbones:
        ca=np.asarray(ca)
        for i in range(len(ca)-2):
            v=np.cross(ca[i+1]-ca[i],ca[i+2]-ca[i]);norm=np.linalg.norm(v)
            if norm>1e-8 and abs(float(v@axis))/norm>1e-4:anchors.append(v/norm);break
    anchor=np.sum(anchors,axis=0) if anchors else np.zeros(3)
    convention='intrinsic_sequence_backbone_normal; representation only'
    if abs(float(anchor@axis))>1e-6:
        if anchor@axis<0:axis=-axis
    else:convention='arbitrary_SVD_sign; +/- are equivalent representations'
    projections=centered@axis;order=np.argsort(projections,kind='stable');ordered=xyz[order];s=projections[order];spacing=np.diff(s);mean=float(spacing.mean());median=float(np.median(spacing));sd=float(spacing.std());cv=sd/max(abs(mean),1e-12)
    lateral=np.diff(ordered,axis=0)-spacing[:,None]*axis;positive=spacing[spacing>1e-6];typical=float(np.median(positive)) if len(positive) else 0.
    paired=any(ds<policy.coincident_projection_ratio*typical and np.linalg.norm(l)>policy.lateral_spacing_ratio*typical for ds,l in zip(spacing,lateral))
    zigzag=median>0 and float(np.median(np.linalg.norm(lateral,axis=1)))>policy.lateral_spacing_ratio*median
    status='REPEAT_AGGREGATE_PASS'
    if variance<policy.min_axis_explained_variance:status='AMBIGUOUS_HOMOMER'
    elif paired or zigzag:status='MULTI_PROTOFILAMENT_UNSUPPORTED'
    elif mean<=0 or np.any(spacing<=1e-6) or cv>policy.max_spacing_cv:status='IRREGULAR_REPEAT_SPACING'
    return RepeatGeometry(axis.tolist(),variance,order.tolist(),projections.tolist(),spacing.tolist(),mean,median,sd,cv,status,convention)

def rigid_rmsd(a,b):return fit(a,b)[2]

def contact_count(a,b,cutoff=8.):
    from scipy.spatial.distance import cdist
    return int((cdist(a,b)<=cutoff).sum())
