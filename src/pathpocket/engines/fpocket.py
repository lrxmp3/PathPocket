import re,subprocess,shutil,json
from pathlib import Path
import numpy as np
from pathpocket.protein.structure import atoms
from pathpocket.core.provenance import sha256

def discover(executable,receptor,out,receptor_id,state_id,top_n=10):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);inp=out/'receptor.pdb';shutil.copy2(receptor,inp)
    command=[str(executable),'-f',str(inp)]
    p=subprocess.run(command,cwd=out,capture_output=True,text=True,timeout=600)
    (out/'stdout.log').write_text(p.stdout);(out/'stderr.log').write_text(p.stderr)
    (out/'invocation.json').write_text(json.dumps(dict(command=command,returncode=p.returncode,input_sha256=sha256(inp)),indent=2))
    info=out/'receptor_out/receptor_info.txt'
    if p.returncode or not info.is_file():raise RuntimeError(f'fpocket failed: see {out}')
    descriptors={};current=None
    for line in info.read_text().splitlines():
        m=re.match(r'\s*Pocket\s+(\d+)\s*:',line)
        if m:current=int(m[1]);descriptors[current]={};continue
        if current and ':' in line:
            k,v=line.split(':',1)
            try:descriptors[current][k.strip()]=float(v.strip())
            except ValueError:pass
    instances=[]
    for rank,desc in sorted(descriptors.items()):
        if rank>top_n:continue
        pocket=out/f'receptor_out/pockets/pocket{rank}_atm.pdb';vertices=out/f'receptor_out/pockets/pocket{rank}_vert.pqr'
        if not pocket.exists() or not vertices.exists():raise RuntimeError('fpocket pocket files incomplete')
        xyz=[]
        for line in vertices.read_text().splitlines():
            if line.startswith(('ATOM','HETATM')):
                fields=line.split();xyz.append([float(x) for x in fields[-5:-2]])
        if not xyz:raise ValueError('No alpha spheres in detected pocket')
        instances.append(dict(region_instance_id=f'{receptor_id}_P{rank:03d}',receptor_id=receptor_id,state_id=state_id,rank=rank,center=np.mean(xyz,axis=0).tolist(),residues=sorted({a['residue'] for a in atoms(pocket)}),descriptors=desc))
    return instances
