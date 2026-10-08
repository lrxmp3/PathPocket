"""Presentation naming and lossless coordinate export. No scientific computation."""
import csv,json,re,hashlib,string,uuid
from pathlib import Path
from decimal import Decimal
from .ux_scene import scene
from .ux_results import digest

def safe_id(value):
 s=re.sub(r'[^A-Za-z0-9_.-]+','_',str(value)).strip('._')
 if not s or len(s)>140:raise ValueError('Unsupported export identifier')
 return s

def filenames(index):
 candidates={};groups={}
 for r in index.rows:
  key=(r['target_id'],r['molecule_id']);suffix=re.search(r'(M\d+)$',r['molecule_id']);suffix=suffix[1] if suffix else safe_id(r['molecule_id'])
  base=safe_id(r.get('region_family_id') or r['target_id'])+'_'+suffix;candidates[key]=(base,suffix);groups.setdefault(base.casefold(),[]).append(key)
 out={};used=set()
 for key in sorted(candidates):
  base,suffix=candidates[key]
  if len(groups[base.casefold()])>1:base=safe_id(key[0])+'_'+suffix
  original=base;n=2
  while base.casefold() in used:base=original+'_'+str(n);n+=1
  used.add(base.casefold());out[key]=base+'.sdf'
 return out

def friendly(index,row):return filenames(index)[(row['target_id'],row['molecule_id'])]

def outside_run(index,directory):
 p=Path(directory).resolve()
 if p.is_relative_to(index.run):raise ValueError('Scientific run is read-only')
 return p

def source_info(index,row):
 p=Path(row['_clean_sdf'] if row.get('_clean_link') else row['_raw_sdf']);record=index.sdf_record(row)
 return dict(source_sdf=str(p),source_sdf_sha256=digest(p),source_record=row.get('source_record'),source_record_basis='raw source_record; clean record selected by molecule_id' if row.get('_clean_link') else 'raw source_record',source_ligand_sha256=hashlib.sha256(record).hexdigest(),original_hash=row['_thumb']),record

def write_molecules(index,directory):
 d=outside_run(index,directory);d.mkdir(parents=True,exist_ok=True);names=filenames(index);items=[]
 for row in index.rows:
  info,record=source_info(index,row);name=names[(row['target_id'],row['molecule_id'])];p=d/name
  if p.exists():
   if p.read_bytes()!=record:raise FileExistsError(p)
  else:
   with p.open('xb') as f:f.write(record)
  item={k:(row.get(k) or 'NA') for k in ['molecule_id','target_id','region_family_id','state_id','physical_compatible','protein_clash','internal_clash','MW','cLogP','TPSA','SA','QED']}
  item.update(friendly_filename=name,canonical_smiles=(row.get('smiles') or 'NA'),Qnorm=(row.get('Q_total_normalized') or 'NA'),sha256=hashlib.sha256(record).hexdigest(),**info);items.append(item)
 indexpath=d/'molecule_index.csv'
 if indexpath.exists():raise FileExistsError(indexpath)
 fields=list(items[0]) if items else ['molecule_id','target_id','region_family_id','state_id','friendly_filename','source_sdf','source_record','canonical_smiles','physical_compatible','protein_clash','internal_clash','Qnorm','MW','cLogP','TPSA','SA','QED','sha256','original_hash','source_sdf_sha256','source_ligand_sha256','source_record_basis']
 with indexpath.open('x',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(items)
 return items

def coordinate_field(raw):
 raw=raw.strip();value=Decimal(raw)
 if not value.is_finite() or len(raw)>8:raise ValueError('Coordinates cannot be represented losslessly in an 8-column PDB field; original SDF remains available.')
 return raw.rjust(8)

def complex_bytes(protein,record):
 lines=protein.decode('ascii').splitlines();plines=[l for l in lines if l.startswith(('ATOM  ','HETATM'))]
 if not plines or any(l.startswith('MODEL ') for l in lines):raise ValueError('A single full-receptor PDB frame is required')
 serials=[int(l[6:11]) for l in plines]
 if len(set(serials))!=len(serials):raise ValueError('Source receptor has duplicate atom serials')
 used_chains={l[21:22] for l in plines};chain=next((c for c in 'Z'+string.ascii_uppercase[:-1]+string.ascii_lowercase+string.digits if c not in used_chains),None)
 if chain is None:raise ValueError('No unused PDB ligand chain identifier')
 for l in plines:
  for a,b in [(30,38),(38,46),(46,54)]:
   if not Decimal(l[a:b]).is_finite():raise ValueError('Invalid source receptor coordinate')
 sl=record.decode('utf-8').splitlines()
 if len(sl)<4 or 'V2000' not in sl[3]:raise ValueError('Existing V2000 SDF required; no conversion performed')
 n,nb=int(sl[3][:3]),int(sl[3][3:6]);last=max(serials+[int(l[6:11]) for l in lines if l.startswith('TER   ') and l[6:11].strip()])
 if last+n>99999:raise ValueError('PDB atom serial capacity exceeded')
 lig=[];element_counts={}
 for i,l in enumerate(sl[4:4+n]):
  element=l[31:34].strip();element_counts[element]=element_counts.get(element,0)+1;name=element+str(element_counts[element])
  if len(name)>4 or not re.fullmatch('[A-Za-z]{1,2}',element):raise ValueError('Unsupported ligand atom label')
  coords=''.join(coordinate_field(l[a:b]) for a,b in [(0,10),(10,20),(20,30)])
  lig.append(f'HETATM{last+i+1:5d} {name:>4s} LIG {chain}   1    '+coords+'  1.00  0.00          '+f'{element:>2s}'+'  ')
 if len(lig)!=n:raise ValueError('Truncated ligand record')
 conect=[]
 for l in sl[4+n:4+n+nb]:
  a,b=int(l[:3]),int(l[3:6])
  if not 1<=a<=n or not 1<=b<=n:raise ValueError('Invalid stored SDF bond index')
  conect.append(f'CONECT{last+a:5d}{last+b:5d}')
 if len(conect)!=nb:raise ValueError('Truncated ligand bonds')
 # Keep every receptor atom and its original columns, including alternates/heteroatoms.
 body=[l for l in lines if l[:6].strip() not in ['END','MASTER']]
 text='REMARK 950 LOSSLESS COORDINATE EXPORT; LIGAND FIELDS MAY USE 4 DECIMALS\n'+'\n'.join(body+lig+conect+['END'])+'\n'
 return text.encode('ascii'),dict(ligand_chain=chain,ligand_residue='LIG',ligand_residue_number=1,ligand_atom_count=n,receptor_atom_count=len(plines),pdb_coordinate_encoding='8-column decimal fields preserving source precision; may exceed standard PDB 3 decimals',connectivity='Stored SDF bond endpoints only; SDF retains bond orders, charges and full chemical identity')

def value(row,key):
 v=row.get(key)
 if v in [None,'','NA','nan']:return None
 if v in ['True','False']:return v=='True'
 try:return float(v)
 except (TypeError,ValueError):return v

def export_complex(index,row,parent):
 # Resolve identity against the loaded immutable index rather than trusting caller paths.
 matches=[r for r in index.rows if (r['target_id'],r['molecule_id'])==(row['target_id'],row['molecule_id'])]
 if len(matches)!=1:raise ValueError('Ambiguous molecule identity')
 row=matches[0];data=scene(index,row['target_id'],row);receptor=Path(data['receptor']);record_info,record=source_info(index,row);pdb,details=complex_bytes(receptor.read_bytes(),record)
 base=Path(friendly(index,row)).stem;parent=outside_run(index,parent);parent.mkdir(parents=True,exist_ok=True);dest=parent/(base+'_export')
 if dest.exists():dest=parent/(base+'_export_'+uuid.uuid4().hex[:8])
 dest.mkdir(exist_ok=False);pdbpath=dest/(base+'_complex.pdb');sdfpath=dest/(base+'_ligand.sdf');infopath=dest/(base+'_info.json')
 info=dict(project=index.summary.get('project'),run_id=index.manifest.get('run_id',index.run.name),target_id=row['target_id'],region_family_id=row.get('region_family_id'),state_id=row.get('state_id'),molecule_id=row['molecule_id'],friendly_filename=base+'.sdf',canonical_smiles=row.get('smiles'),center_A=data['center'],fpocket_rank=data['rank'],lining_residues=data['lining_residues'],repeat_offsets=sorted(data['chains'].values()),source_receptor=str(receptor),source_receptor_sha256=digest(receptor),coordinate_preserving=True,**record_info,**details)
 for key in ['physical_compatible','protein_clash','internal_clash','MW','cLogP','TPSA','SA','QED']:info[key]=value(row,key)
 info['Qnorm']=value(row,'Q_total_normalized');info['predicted_ED_volume']=data['metrics'].get('predicted_ED_volume');info['source_run']=str(index.run);info['scientific_operations_performed']=[];info['scientific_boundary']='Generated conformation, not a validated binding pose; no docking, minimization, protonation or chemical recomputation.'
 info['outputs']={pdbpath.name:hashlib.sha256(pdb).hexdigest(),sdfpath.name:hashlib.sha256(record).hexdigest()}
 with pdbpath.open('xb') as f:f.write(pdb)
 with sdfpath.open('xb') as f:f.write(record)
 with infopath.open('x',encoding='utf-8') as f:json.dump(info,f,ensure_ascii=False,indent=2)
 return dest
