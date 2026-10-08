"""Heavy-atom PDB QC and conservative residue-identity alignment."""
from pathlib import Path
import numpy as np

def atoms(path):
    result=[];models=0
    for line in Path(path).read_text().splitlines():
        if line.startswith('MODEL '):
            models+=1
            if models>1:raise ValueError('Multi-model PDB must be split into separate structures')
        if not line.startswith('ATOM  ') or line[16:17] not in [' ','A']:continue
        element=line[76:78].strip() or line[12:16].strip()[0]
        if element in ['H','D']:continue
        xyz=np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
        if not np.isfinite(xyz).all():raise ValueError('Nonfinite receptor coordinates')
        key=f'{line[21:22].strip() or "_"}:{line[22:26].strip()}:{line[26:27].strip() or "_"}'
        result.append(dict(line=line,residue=key,resname=line[17:20],atom=line[12:16].strip(),element=element,xyz=xyz))
    if not result:raise ValueError(f'No protein heavy atoms in {path}')
    keys=[(a['residue'],a['atom']) for a in result]
    if len(set(keys))!=len(keys):raise ValueError(f'Duplicate atoms/alternate locations in {path}; clean input explicitly')
    return result

def ca_map(records):return {a['residue']:(a['resname'],a['xyz']) for a in records if a['atom']=='CA'}

def fit(mobile,reference):
    mobile=np.asarray(mobile);reference=np.asarray(reference)
    if len(mobile)<3 or np.linalg.matrix_rank(mobile-mobile.mean(0))<2:raise ValueError('At least 3 noncollinear matched CA atoms required')
    x=mobile-mobile.mean(0);y=reference-reference.mean(0)
    u,_,vt=np.linalg.svd(x.T@y);correction=np.eye(3);correction[-1,-1]=np.linalg.det(u@vt)
    rotation=u@correction@vt;translation=reference.mean(0)-mobile.mean(0)@rotation
    rmsd=float(np.sqrt(((mobile@rotation+translation-reference)**2).sum(1).mean()))
    return rotation,translation,rmsd

def transform(records,rotation,translation,out,center=None,radius=30):
    transformed=[(a,a['xyz']@rotation+translation) for a in records]
    keep={a['residue'] for a,x in transformed if center is None or np.linalg.norm(x-np.asarray(center))<=radius}
    with Path(out).open('w') as f:
        for a,x in transformed:
            if a['residue'] in keep:
                line=a['line'];f.write(line[:30]+''.join(f'{v:8.3f}' for v in x)+line[54:]+'\n')
        f.write('END\n')
    if not keep:raise ValueError('Empty receptor crop')

def align(records,reference):
    a=ca_map(records);b=ca_map(reference);common=sorted(k for k in a.keys()&b.keys() if a[k][0]==b[k][0])
    if len(common)<3:raise ValueError('Insufficient matching chain/residue IDs; sequence remapping is not implemented in v0.1')
    r,t,rmsd=fit([a[k][1] for k in common],[b[k][1] for k in common])
    return r,t,dict(common_CA=len(common),matched_fraction=len(common)/max(len(a),len(b)),rmsd_A=rmsd,method='same chain/residue/insertion code and residue identity')
