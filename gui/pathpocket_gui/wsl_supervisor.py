"""Transport/process lifecycle only; calls the unmodified CLI. Runs with WSL stdlib Python."""
import json, os, signal, subprocess, sys, time
from pathlib import Path

def put(path,data):
    # Windows readers can briefly deny delete-sharing on a DrvFS JSON file.
    # Keep the previous complete record until atomic replacement succeeds.
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    for attempt in range(30):
        try:tmp.replace(path);return
        except PermissionError:
            if attempt==29:raise
            time.sleep(min(.05*(attempt+1),.25))

def heartbeat(folder,result):
    try:put(folder/'state.json',result)
    except OSError as e:
        # A failed presentation heartbeat must not abandon the owned child.
        result['state_write_warning']=str(e)


def process_identity(pid):
    try:
        raw=(Path('/proc')/str(pid)/'stat').read_text();fields=raw[raw.rfind(')')+2:].split()
        return (fields[0],int(fields[1]),fields[19])
    except (OSError,ValueError,IndexError):return None

def descendants(parent):
    processes={}
    for path in Path('/proc').glob('[0-9]*/stat'):
        pid=int(path.parent.name);identity=process_identity(pid)
        if identity:processes[pid]=identity
    children={parent};changed=True
    while changed:
        before=len(children);children.update(pid for pid,identity in processes.items() if identity[1] in children);changed=len(children)>before
    return {pid:processes[pid][2] for pid in children-{parent} if pid in processes}

def signal_descendants(identities,sig):
    remaining=[]
    for pid,start in identities.items():
        current=process_identity(pid)
        if not current or current[2]!=start or current[0]=='Z':continue
        try:os.kill(pid,sig)
        except ProcessLookupError:continue
        except PermissionError:remaining.append(pid)
    return remaining

def observe_ed2mol(parent):
    processes={}
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            text=path.read_text();tail=text[text.rfind(')')+2:].split();processes[int(path.parent.name)]=int(tail[1])
        except (OSError,ValueError,IndexError):pass
    children={parent};changed=True
    while changed:
        before=len(children);children.update(pid for pid,ppid in processes.items() if ppid in children);changed=len(children)>before
    found=[]
    for pid in children-{parent}:
        try:
            argv=(Path('/proc')/str(pid)/'cmdline').read_bytes().decode().strip('\0').split('\0')
            if any(arg.endswith('/tests/run_generation.py') for arg in argv):found.append(dict(pid=pid,argv=argv,observed_at=time.time()))
        except (OSError,UnicodeError):pass
    return found

def main(request):
    p=Path(request);job=json.loads(p.read_text());folder=p.parent
    result=dict(status='RUNNING',command=job['command'],run_path=None)
    output=Path(job['project'])/'runs' if job.get('project') else None
    before=set(output.glob('RUN_*')) if output and output.exists() else set()
    lock=None
    if job['command'] in ['run','run-engineering-no-targets','discover','challenge','analyze','report'] and output:
        lock=Path(job['project'])/'.pathpocket_gui.lock'
        try:
            with lock.open('x') as f: f.write(str(os.getpid()))
        except FileExistsError:
            put(folder/'response.json',dict(status='FAIL',error='Another GUI run holds the project lock; inspect the existing task before removing a stale lock.'));return 1
    try:
        os.environ['PATHPOCKET_USER_HOME']=job['workspace']
        os.environ['PATHPOCKET_WORKSPACE']=job['workspace']
        put(folder/'environment.json',dict(PATHPOCKET_WORKSPACE=job['workspace'],PATHPOCKET_USER_HOME=job['workspace']))
        argv=([sys.executable,job['fixture_runner']]+job.get('arguments',[])) if job['command']=='run-engineering-no-targets' else [job['launcher'],job['command']]+job.get('arguments',[])
        with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
            proc=subprocess.Popen(argv,stdout=out,stderr=err,start_new_session=True)
            result['pid']=proc.pid;result['ed2mol_started']=False;heartbeat(folder,result)
            cancelled=False;sent=0;cancelled_children={}
            while proc.poll() is None:
                observed=observe_ed2mol(proc.pid) if job['command'] in ['run','run-engineering-no-targets'] else []
                if observed:
                    result['ed2mol_started']=True;put(folder/'ed2mol_processes.json',observed)
                if output and output.exists():
                    found=sorted(set(output.glob('RUN_*'))-before)
                    if len(found)==1:result['run_path']=str(found[0])
                    elif len(found)>1:
                        result['run_path']=None;result['discovery_warning']='Multiple new runs; refusing ambiguous association'
                if (folder/'cancel.json').exists():
                    if not cancelled:
                        cancelled=True;sent=time.monotonic()
                        cancelled_children=descendants(proc.pid)
                        signal_descendants(cancelled_children,signal.SIGTERM)
                        os.killpg(proc.pid,signal.SIGINT)
                    elif time.monotonic()-sent>15:
                        try:os.killpg(proc.pid,signal.SIGKILL if time.monotonic()-sent>45 else signal.SIGTERM)
                        except ProcessLookupError:pass
                heartbeat(folder,result);time.sleep(.5)
        if output and output.exists() and not result['run_path']:
            found=sorted(set(output.glob('RUN_*'))-before)
            if len(found)==1:result['run_path']=str(found[0])
        if result.get('run_path'):
            for record in Path(result['run_path']).glob('06_CHEMICAL_CHALLENGE/**/execution.json'):
                try:
                    evidence=json.loads(record.read_text())
                    if 'returncode' in evidence and any(str(a).endswith('/tests/run_generation.py') for a in evidence.get('command',[])):result['ed2mol_started']=True
                except (OSError,ValueError):pass
        result.update(status='INTERRUPTED' if cancelled else ('PASS' if proc.returncode==0 else 'FAIL'),returncode=proc.returncode)
        if cancelled:
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            deadline=time.monotonic()+2
            while time.monotonic()<deadline and any((identity:=process_identity(pid)) and identity[2]==start and identity[0]!='Z' for pid,start in cancelled_children.items()):time.sleep(.05)
            denied=signal_descendants(cancelled_children,signal.SIGKILL)
            deadline=time.monotonic()+1
            while time.monotonic()<deadline and any((identity:=process_identity(pid)) and identity[2]==start and identity[0]!='Z' for pid,start in cancelled_children.items()):time.sleep(.05)
            survivors=[pid for pid,start in cancelled_children.items() if (identity:=process_identity(pid)) and identity[2]==start and identity[0]!='Z']
            result['cancelled_descendants_checked']=len(cancelled_children)
            if denied or survivors:
                result['status']='FAIL';result['error']='Cancellation could not confirm child process termination; inspect the local task logs.'
                result['cancel_cleanup_unconfirmed']=sorted(set(denied+survivors))
        if job['command'] in ['doctor','validate','status']:
            # This is the CLI's JSON API response, never terminal-word matching.
            try:result['data']=json.loads((folder/'stdout.log').read_text(encoding='utf-8'))
            except ValueError:
                if proc.returncode==0:raise ValueError('Structured CLI JSON response missing')
        if job['command']=='doctor' and proc.returncode==0:
            version=subprocess.run([job['launcher'],'--version'],capture_output=True,text=True,timeout=30)
            result['backend_version']=version.stdout.strip() if version.returncode==0 else 'unavailable'
        if proc.returncode!=0:
            original=(folder/'stderr.log').read_text(encoding='utf-8',errors='replace')[-10000:]
            result['error']=(result.get('error','')+'\n'+original).strip()
        put(folder/'response.json',result);return 0
    except Exception as e:
        result.update(status='FAIL',error=str(e));put(folder/'response.json',result);return 1
    finally:
        if lock and lock.exists():lock.unlink()

if __name__=='__main__':sys.exit(main(sys.argv[1]))
