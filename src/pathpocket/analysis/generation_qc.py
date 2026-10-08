"""Explicit basic QC; geometry compatibility is not evidence of binding."""
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from pathpocket.protein.structure import atoms
from .descriptors import describe

def analyze_target(folder,target,requested):
    folder=Path(folder);ed=np.load(folder/'raw/ligED.npy');positive=ed[ed[:,3]>0];tree=cKDTree(ed[:,:3]);peak=float(positive[:,3].max())
    protein=atoms(folder/'receptor_full.pdb');px=np.array([a['xyz'] for a in protein]);pt=Chem.GetPeriodicTable();pr=np.array([pt.GetRvdw(a['element']) for a in protein])
    rows=[];seen=set();molecules={};writer=Chem.SDWriter(str(folder/'clean_output.sdf'))
    supplier=Chem.SDMolSupplier(str(folder/'raw/output.sdf'),sanitize=False,removeHs=False) if (folder/'raw/output.sdf').stat().st_size else []
    for i,m in enumerate(supplier):
        row=dict(molecule_id=target['target_id']+f'_M{i+1:06d}',target_id=target['target_id'],region_family_id=target['region_family_id'],state_id=target['state_id'],source_record=i+1,readable=m is not None,sanitized=False,valid_3D=False,valid=False,unique=False,physical_compatible=False)
        if m is None:rows.append(row);continue
        try:Chem.SanitizeMol(m);row['sanitized']=True
        except Exception as exc:row['error']=str(exc);rows.append(row);continue
        if not m.GetNumConformers():rows.append(row);continue
        xyz=m.GetConformer().GetPositions();bonds=[np.linalg.norm(xyz[b.GetBeginAtomIdx()]-xyz[b.GetEndAtomIdx()]) for b in m.GetBonds()]
        row['valid_3D']=bool(m.GetConformer().Is3D() and np.isfinite(xyz).all() and np.ptp(xyz,axis=0).max()>.1)
        row['valid']=bool(row['valid_3D'] and bonds and min(bonds)>=.5 and max(bonds)<=3 and len(Chem.GetMolFrags(m))==1 and all(a.GetAtomicNum()>0 for a in m.GetAtoms()))
        if not row['valid']:rows.append(row);continue
        smiles=Chem.MolToSmiles(m,isomericSmiles=True);row.update(smiles=smiles,unique=smiles not in seen);seen.add(smiles)
        row.update(describe(m));heavy=[a.GetIdx() for a in m.GetAtoms() if a.GetAtomicNum()>1];n=len(heavy);hx=xyz[heavy]
        rho=ed[tree.query(hx)[1],3];raw=float(m.GetProp('qscore')) if m.HasProp('qscore') else float('nan')
        coverage=float((cKDTree(hx).query(positive[:,:3])[0]<=1.5).mean())
        row.update(heavy_atoms=n,Q_total_raw=raw,Q_total_normalized=raw/n/peak,ED_coverage=coverage,ED_coverage_per_heavy_atom=coverage/n)
        lr=np.array([pt.GetRvdw(m.GetAtomWithIdx(i).GetAtomicNum()) for i in heavy]);protein_clash=bool((cdist(hx,px)<.75*(lr[:,None]+pr[None,:])).any())
        graph=Chem.GetDistanceMatrix(m)[np.ix_(heavy,heavy)];internal=bool((np.triu(graph>=3,1)&(cdist(hx,hx)<.65*(lr[:,None]+lr[None,:]))).any())
        row.update(protein_clash=protein_clash,internal_clash=internal,physical_compatible=not protein_clash and not internal)
        row['upstream_name']=m.GetProp('_Name') if m.HasProp('_Name') else '';row['isotope_tags']=sum(a.GetIsotope()!=0 for a in m.GetAtoms())
        rows.append(row)
        if row['unique']:
            m.SetProp('molecule_id',row['molecule_id']);writer.write(m);molecules[row['molecule_id']]=m
    writer.close();df=pd.DataFrame(rows)
    for col in ['molecule_id','target_id','region_family_id','state_id','source_record']:
        if col not in df:df[col]=pd.Series(dtype='object')
    for col in ['readable','sanitized','valid_3D','valid','unique','physical_compatible']:
        if col not in df:df[col]=pd.Series(dtype='bool')
    df.to_csv(folder/'molecule_qc.csv',index=False);good=df[df.valid & df.unique]
    summary=dict(target_id=target['target_id'],region_family_id=target['region_family_id'],state_id=target['state_id'],requested=requested,generated=len(df),readable=int(df.readable.sum()),sanitized=int(df.sanitized.sum()),valid_3D=int(df.valid_3D.sum()),valid=int(df.valid.sum()),unique=len(good),duplicate_fraction=1-len(good)/max(1,int(df.valid.sum())),physical_compatible=int(good.physical_compatible.sum()),clash_rate=float(good.protein_clash.mean()) if len(good) else None,heavy_atom_min=int(good.heavy_atoms.min()) if len(good) else None,heavy_atom_max=int(good.heavy_atoms.max()) if len(good) else None,formal_charge_distribution={str(k):int(v) for k,v in good.formal_charge.value_counts().items()} if len(good) else {},predicted_ED_volume=float(len(positive)*.125),median_Q_normalized=float(good.Q_total_normalized.median()) if len(good) else None)
    return df,summary,molecules
