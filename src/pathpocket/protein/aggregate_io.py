"""Strict observed polymer ingestion for the structural adapter, not a new science parser."""
from pathlib import Path
import numpy as np
from .structure import atoms
from .residue_mapping import AA,MappingError

def read_polymer(path):
    path=Path(path)
    if path.suffix.lower() not in ['.cif','.mmcif']:records=atoms(path)
    else:
        from Bio.PDB.MMCIF2Dict import MMCIF2Dict
        data=MMCIF2Dict(str(path));n=len(data['_atom_site.group_PDB']);records=[]
        def value(key,i,default=''):
            column=data.get('_atom_site.'+key);return column[i] if column else default
        models={value('pdbx_PDB_model_num',i,'1') for i in range(n) if value('group_PDB',i)=='ATOM'}
        if len(models)!=1:raise ValueError('Adapter requires one experimental model; no silent model selection')
        for i in range(n):
            if value('group_PDB',i)!='ATOM' or value('label_alt_id',i) not in ['.','?','A','']:continue
            element=value('type_symbol',i).upper()
            if element in ['H','D']:continue
            chain=value('label_asym_id',i);num=value('label_seq_id',i)
            if num in ['.','?','']:raise ValueError('Polymer atom lacks label_seq_id')
            xyz=np.array([float(value('Cartn_'+axis,i)) for axis in 'xyz']);name=value('label_comp_id',i);atom=value('label_atom_id',i)
            records.append(dict(residue=f'{chain}:{num}:_',resname=name,atom=atom,element=element,xyz=xyz,auth_chain=value('auth_asym_id',i),auth_residue=value('auth_seq_id',i),occupancy=float(value('occupancy',i,'1')),bfactor=float(value('B_iso_or_equiv',i,'0')),line=None))
    if not records:raise ValueError('No observed polymer heavy atoms')
    keys=[(a['residue'],a['atom']) for a in records]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate polymer atom identifiers')
    chains={}
    for a in records:
        if not np.isfinite(a['xyz']).all():raise ValueError('Nonfinite coordinates')
        if a['resname'].strip() not in AA:raise MappingError('UNSUPPORTED_RESIDUE','Nonstandard ATOM residue '+a['resname'])
        chain,num,ins=a['residue'].split(':');a=dict(a,chain=chain,number=int(num),insertion=ins);chains.setdefault(chain,[]).append(a)
    # Order-independent ingestion. Chain order has no role in geometry or assignment.
    for chain in chains:chains[chain].sort(key=lambda a:(a['number'],a['insertion'],a['atom']))
    return chains

def residues(records):
    seen={}
    for a in records:
        if a['residue'] in seen and seen[a['residue']]['resname']!=a['resname'].strip():raise ValueError('Conflicting residue names')
        seen.setdefault(a['residue'],dict(raw_id=a['residue'],resname=a['resname'].strip(),aa=AA[a['resname'].strip()]))
    return list(seen.values())
