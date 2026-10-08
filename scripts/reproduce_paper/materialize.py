"""Restore deduplicated, public data paths into a new workspace; never runs science."""
from pathlib import Path
import argparse,csv,hashlib,shutil,os
p=argparse.ArgumentParser();p.add_argument('data',type=Path);p.add_argument('output',type=Path);p.add_argument('--group',default='');a=p.parse_args()
data=a.data.resolve();out=a.output.resolve()
if out.exists():raise SystemExit('Output must not exist; choose a fresh workspace.')
out.mkdir(parents=True)
rows=list(csv.DictReader((data/'10_METADATA/PUBLIC_FILE_MAP.csv').open(encoding='utf-8-sig')))
count=0
for r in rows:
 if a.group and not r['public_name'].startswith(a.group+'/'):continue
 src=(data/r['stored_file']).resolve();relative=r['original_path']
 if '<' in relative or ':' in relative:continue
 dest=(out/relative).resolve()
 if not src.is_relative_to(data) or not dest.is_relative_to(out):raise ValueError('Unsafe manifest path')
 raw=src.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=r['public_sha256']:raise ValueError('Checksum mismatch '+r['stored_file'])
 # Windows long-path spelling is applied only after validating the resolved destination.
 io_dest=Path('\\\\?\\'+str(dest)) if os.name=='nt' else dest
 io_dest.parent.mkdir(parents=True,exist_ok=True)
 # Only script roots are parameterized. Raw numeric/source files retain their public bytes.
 if src.suffix in ['.py','.mjs','.js','.sh','.tcl','.pml']:
  try:raw=raw.decode('utf8').replace('<WORKSPACE>',out.as_posix()).encode('utf8')
  except UnicodeError:pass
 if io_dest.exists() and io_dest.read_bytes()!=raw:raise ValueError('Conflicting original path '+relative)
 io_dest.write_bytes(raw);count+=1
print('Restored',count,'logical files; no scientific workflow or renderer executed.')
