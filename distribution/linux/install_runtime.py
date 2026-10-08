"""First-run downloads into this distribution only; no system Python/Conda changes."""
from pathlib import Path
import sys,os,json,hashlib,urllib.request,subprocess,zipfile,shutil,time
B=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def acquire(x,folder):
    folder.mkdir(parents=True,exist_ok=True);p=folder/x.get('filename',x['url'].split('/')[-1])
    if p.exists() and sha(p)==x['sha256']:return p
    print('正在获取 '+p.name,flush=True)
    req=urllib.request.Request(x['url'],headers={'User-Agent':'PathPocket-EasyDeploy-1.0'})
    tmp=p.with_suffix(p.suffix+'.partial')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=120) as r,tmp.open('wb') as f:
                while b:=r.read(4*1024*1024):f.write(b)
            if sha(tmp)!=x['sha256']:raise RuntimeError('下载文件校验失败：'+p.name)
            break
        except Exception:
            if attempt==2:raise
            print('下载中断，正在自动重试（'+str(attempt+2)+'/3）：'+p.name,flush=True)
            time.sleep(3)
    tmp.replace(p);return p
def extract_zip(p,dest):
    with zipfile.ZipFile(p) as z:
        for n in z.namelist():
            if not (dest/n).resolve().is_relative_to(dest.resolve()):raise RuntimeError('Unsafe archive path')
        z.extractall(dest)
def main():
    lock=json.loads((B/'download-lock.json').read_text());cache=B/'runtime/downloads'
    if os.name=='nt':
        site=Path(sys.executable).parent/'Lib/site-packages';site.mkdir(parents=True,exist_ok=True)
        for x in lock['windows']:extract_zip(acquire(x,cache),site)
        return
    os.environ.update(PYTHONNOUSERSITE='1',PYTHONPATH='',PYTHONDONTWRITEBYTECODE='1',PIP_NO_CACHE_DIR='1',PIP_DISABLE_PIP_VERSION_CHECK='1')
    wheels=[acquire(x,cache) for x in lock['linux']]
    subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps',*[str(x) for x in wheels]],check=True)
    subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps',str(B/'payload/backend/pathpocket-0.3.0-py3-none-any.whl')],check=True)
    shutil.copy2(B/'sitecustomize.py',Path(sys.prefix)/'lib/python3.11/site-packages/sitecustomize.py')
    w=json.loads((B/'weights-lock.json').read_text());archive=acquire(dict(url=w['url'],sha256=w['archive_sha256'],filename='weights.zip'),cache)
    weights=B/'payload/engine/weights';weights.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for name,expected in w['weights'].items():
            entries=[n for n in z.namelist() if Path(n).name==name]
            if len(entries)!=1:raise RuntimeError('权重压缩包结构不符')
            data=z.read(entries[0]);assert hashlib.sha256(data).hexdigest()==expected
            (weights/name).write_bytes(data)
    fp=acquire(lock['fpocket'],cache);dest=B/'runtime/fpocket'
    if not dest.exists():subprocess.run([str(B/'runtime/tools/bin/micromamba'),'package','extract',str(fp),str(dest)],check=True)
    if sha(dest/'bin/fpocket')!=json.loads((B/'release_manifest.json').read_text())['fpocket_sha256']:raise RuntimeError('fpocket 与冻结版本不一致')
    sm=acquire(lock['smina'],cache);shutil.copy2(sm,B/'payload/engine/utils/smina.static');(B/'payload/engine/utils/smina.static').chmod(0o755)
    print('运行环境与权重安装完成。正在检查 GPU。',flush=True)
if __name__=='__main__':main()
