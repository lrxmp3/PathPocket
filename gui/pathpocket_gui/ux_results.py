"""Read-only CSV/SDF index. Never computes a scientific descriptor or QC value."""
import csv,json,re,hashlib,io
from pathlib import Path
FIELDS=['molecule_id','target_id','state_id','region_family_id','valid','unique','physical_compatible','protein_clash','internal_clash','Q_total_raw','Q_total_normalized','ED_coverage','MW','cLogP','TPSA','HBD','HBA','rotatable_bonds','ring_count','aromatic_ring_count','fractionCSP3','formal_charge','SA','QED','PAINS','Brenk','scaffold','cluster_id']
def truth(v):return str(v).lower()=='true'
def read_json(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
    if not Path(p).exists():return []
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def records(path):
    raw=Path(path).read_bytes();ends=[m.end() for m in re.finditer(rb'(?m)^\$\$\$\$\r?\n?',raw)];starts=[0]+ends[:-1]
    return [raw[a:b] for a,b in zip(starts,ends)]
def thumb_id(row):return hashlib.sha256((row['target_id']+'\0'+row['molecule_id']).encode()).hexdigest()[:24]

class ResultIndex:
    def __init__(self,run):
        self.run=Path(run).resolve();self.manifest=read_json(self.run/'run_manifest.json');self.artifacts=read_json(self.run/'artifacts.json')
        summaries=[self.safe(a['path']) for a in self.artifacts if Path(a['path']).name=='summary.json']
        if len(summaries)!=1:raise ValueError('Missing/ambiguous summary contract')
        self.summary=read_json(summaries[0]);self.source_files={summaries[0],self.run/'run_manifest.json',self.run/'artifacts.json'}
        self.rows=[];keys=set();clusters={(r['target_id'],r['molecule_id']):r for r in rows(self.run/'07_ANALYSIS/cluster_assignments.csv')}
        qc_files=sorted(self.run.glob('06_CHEMICAL_CHALLENGE/*/molecule_qc.csv'))
        for path in qc_files:
            self.source_files.add(path);folder=path.parent;raw=folder/'raw/output.sdf';clean=folder/'clean_output.sdf'
            count=len(records(raw)) if raw.exists() else 0
            clean_ids={}
            if clean.exists():
                for record in records(clean):
                    match=re.search(rb'>\s*<molecule_id>[^\n]*\r?\n([^\r\n]+)',record)
                    if match:clean_ids[match[1].decode()]=record
            for row in rows(path):
                key=(row['target_id'],row['molecule_id'])
                if key in keys:raise ValueError('Duplicate target/molecule key')
                keys.add(key)
                if row['target_id']!=folder.name:raise ValueError('Molecule belongs to a different target')
                source=int(row['source_record'])
                if not 1<=source<=count:raise ValueError('SDF record index mismatch')
                row.update({k:v for k,v in clusters.get(key,{}).items() if k not in row})
                row.update(_target_folder=str(folder),_raw_sdf=str(raw),_clean_sdf=str(clean),_csv=str(path),_clean_link=row['molecule_id'] in clean_ids,_thumb=thumb_id(row))
                self.rows.append(row)
            self.source_files.update(p for p in [raw,clean] if p.exists())
        for p in (self.run/'07_ANALYSIS').glob('*.csv'):self.source_files.add(p)
        self.source_hashes={str(p.relative_to(self.run)):digest(p) for p in sorted(self.source_files)}
        self.targets=self.summary.get('targets',[])
        self.figures=self.summary.get('figures',[])
    def safe(self,value):
        p=(self.run/value).resolve()
        if not p.is_relative_to(self.run):raise ValueError('Artifact outside run')
        return p
    def filtered(self,target='',state='',qc='all',search=''):
        result=[]
        for r in self.rows:
            if target and r['target_id']!=target or state and r['state_id']!=state:continue
            if qc=='valid_unique' and not (truth(r.get('valid')) and truth(r.get('unique'))):continue
            if qc=='physical_compatible' and not truth(r.get('physical_compatible')):continue
            if qc=='clash' and not (truth(r.get('protein_clash')) or truth(r.get('internal_clash'))):continue
            if search and search.lower() not in (r['molecule_id']+' '+r.get('smiles','')).lower():continue
            result.append(r)
        return result
    def unchanged(self):return all(digest(self.run/k)==v for k,v in self.source_hashes.items())
    def figure_members(self,figure):
        source=rows(self.run/'08_REPORT'/figure.get('source','missing.csv'));selected={}
        for cell in source:
            keys=[k for k in ['molecule_id','target_id','state_id','region_family_id'] if cell.get(k)]
            if not keys:continue
            for r in self.filtered(qc='valid_unique'):
                if all(r.get(k)==cell[k] for k in keys):selected[(r['target_id'],r['molecule_id'])]=r
        return list(selected.values())
    def export_csv(self,selected,dest):
        dest=Path(dest)
        if dest.is_relative_to(self.run):raise ValueError('Original run is read-only')
        fields=list(dict.fromkeys(k for r in selected for k in r if not k.startswith('_')))
        with dest.open('x',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(selected)
    def export_sdf(self,selected,dest):
        dest=Path(dest)
        if dest.is_relative_to(self.run):raise ValueError('Original run is read-only')
        cache={};content=[]
        for row in selected:
            content.append(self.sdf_record(row,cache))
        with dest.open('xb') as f:f.write(b''.join(content))
    def sdf_record(self,row,cache=None):
        cache=cache if cache is not None else {}
        if row.get('_clean_link'):
            clean=row['_clean_sdf']
            if clean not in cache:cache[clean]=records(clean)
            match=[]
            for record in cache[clean]:
                field=re.search(rb'>\s*<molecule_id>[^\n]*\r?\n([^\r\n]+)',record)
                if field and field[1].decode()==row['molecule_id']:match.append(record)
            if len(match)!=1:raise ValueError('Ambiguous clean SDF identity')
            return match[0]
        raw=row['_raw_sdf']
        if raw not in cache:cache[raw]=records(raw)
        return cache[raw][int(row['source_record'])-1]

def write_index(index,directory):
    directory=Path(directory)
    if directory.resolve().is_relative_to(index.run):raise ValueError('Presentation must be outside original run')
    directory.mkdir(parents=True,exist_ok=True)
    p=directory/'result_index.json'
    from .ux_i18n import figure_title
    for f in index.figures:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',f['name']):raise ValueError('Unsafe figure identifier')
    plots=[dict(name=f['name'],source=f.get('source'),values=rows(index.safe('08_REPORT/'+f.get('source','missing.csv'))),titles={lang:figure_title(f['name'],lang) for lang in ['zh','en']}) for f in index.figures]
    p.write_text(json.dumps(dict(run=str(index.run),summary=index.summary,rows=index.rows,plots=plots,source_sha256=index.source_hashes),ensure_ascii=False,indent=2),encoding='utf-8')
    return p
