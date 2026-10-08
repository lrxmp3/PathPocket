"""Artifact-only structure scene. No pose generation, alignment, contacts or descriptors."""
import json,os,math
from pathlib import Path
from .ux_results import read_json,rows,digest

def pdb_atoms(path):
 result=[]
 for line in Path(path).read_text().splitlines():
  if line.startswith('ENDMDL'):break
  if line[:6].strip() not in ['ATOM','HETATM'] or line[16:17] not in [' ','A']:continue
  xyz=[float(line[a:b]) for a,b in [(30,38),(38,46),(46,54)]]
  if not all(math.isfinite(x) for x in xyz):raise ValueError('Non-finite coordinates')
  result.append(dict(xyz=xyz,name=line[12:16].strip(),chain=line[21:22],residue=line[22:26].strip(),icode=line[26:27].strip() or '_',resname=line[17:20].strip(),element=line[76:78].strip()))
 return result

def sdf_geometry(record):
 lines=record.decode('utf-8',errors='replace').splitlines()
 if 'V2000' not in lines[3]:raise ValueError('3D viewer supports existing V2000 records only; open original SDF for this format.')
 n,m=int(lines[3][:3]),int(lines[3][3:6]);atoms=[]
 for line in lines[4:4+n]:
  xyz=[float(line[a:b]) for a,b in [(0,10),(10,20),(20,30)]]
  if not all(math.isfinite(x) for x in xyz):raise ValueError('Non-finite coordinates')
  atoms.append(dict(xyz=xyz,element=line[31:34].strip()))
 bonds=[(int(l[:3])-1,int(l[3:6])-1,int(l[6:9])) for l in lines[4+n:4+n+m]]
 if any(a<0 or b<0 or a>=n or b>=n for a,b,o in bonds):raise ValueError('SDF bond bounds')
 return atoms,bonds

def scene(index,tid,row=None):
 target=next(t for t in index.targets if t['target_id']==tid)
 if row and row['target_id']!=tid:raise ValueError('Molecule/target mismatch')
 folder=index.safe('05_TARGET_SELECTION/'+tid);pdb=folder/'full_receptor.pdb'
 if not pdb.exists():pdb=index.safe('06_CHEMICAL_CHALLENGE/'+tid+'/receptor_full.pdb')
 atoms=pdb_atoms(pdb);center=target.get('center');sources={str(pdb.relative_to(index.run)):digest(pdb)}
 if not isinstance(center,list) or len(center)!=3 or not all(math.isfinite(float(x)) for x in center):raise ValueError('Missing valid target center')
 refpath=index.run/'00_INPUTS/region_reference.json';ref=read_json(refpath) if refpath.exists() else {}
 fam=next((f for f in ref.get('families',[]) if f['region_family_id']==target.get('region_family_id')),None)
 if not fam:fam=next((f for f in index.summary.get('selected_region_families',[]) if f['region_family_id']==target.get('region_family_id')),{})
 canonical=set(fam.get('consensus_residues',[]));mapping={};chains={};mp=index.run/'01_VALIDATE/aggregate'/target.get('receptor_id','')/'local_unit_manifest.json'
 if mp.exists():
  manifest=read_json(mp);sources[str(mp.relative_to(index.run))]=digest(mp)
  mapping={r['prepared_residue_id']:r['canonical_repeat_id'] for r in manifest.get('residue_mapping',[])}
  chains={r['prepared_chain_id']:r['repeat_offset'] for r in manifest.get('prepared_chains',[])}
 # Only persisted identities are highlighted. Missing mapping remains explicit.
 for a in atoms:
  key=a['chain']+':'+a['residue']+':'+a['icode'];a['canonical']=mapping.get(key,key);a['lining']=a['canonical'] in canonical;a['offset']=chains.get(a['chain'])
 rank=target.get('fpocket_rank',target.get('rank'));rank_source=None
 provenance=ref.get('provenance',{});expected=provenance.get('source_sha256','')
 metadata=Path(os.environ.get('PATHPOCKET_FRONTEND_BUNDLE',''))/'assets/metadata'/(expected+'.json')
 if len(expected)==64 and metadata.exists() and digest(metadata)==expected:
  candidates=read_json(metadata)
  match=[r for r in candidates if r.get('region_instance_id') in fam.get('members',[]) and r.get('center')==target.get('center')]
  if len(match)==1:rank=match[0].get('rank');rank_source=expected
 if refpath.exists():sources[str(refpath.relative_to(index.run))]=digest(refpath)
 ligand,bonds=sdf_geometry(index.sdf_record(row)) if row else ([],[])
 gs=next((v for v in index.summary.get('generation_summary',[]) if v['target_id']==tid),{})
 return dict(target=target,atoms=atoms,center=center,chains=chains,lining_residues=sorted(canonical),matched_lining=sorted({a['canonical'] for a in atoms if a['lining']}),rank=rank,rank_source_sha256=rank_source,ligand=ligand,bonds=bonds,molecule=row,metrics=gs,sources=sources,receptor=str(pdb))
