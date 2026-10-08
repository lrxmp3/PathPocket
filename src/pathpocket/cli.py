"""Thin CLI: no scientific algorithms live here."""
import argparse,json,sys
from pathpocket import __version__

def main(argv=None):
    parser=argparse.ArgumentParser(prog='pathpocket');parser.add_argument('--version',action='version',version=__version__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    for name in ['init','validate','discover','challenge','analyze','report','run','status']:
        p=sub.add_parser(name);p.add_argument('path')
        if name in ['analyze','report']:p.add_argument('--from-run')
    args=parser.parse_args(argv)
    try:
        if args.command=='doctor':
            from .core.doctor import doctor
            result=doctor();print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
        if args.command=='init':
            from .core.project import initialize
            print(initialize(args.path));return 0
        if args.command=='status':
            from .core.project import status
            print(json.dumps(status(args.path),indent=2));return 0
        from .config.loader import load_config
        config=load_config(args.path)
        if args.command=='validate':print(json.dumps(dict(passed=True,project=config.name,states=list(config.states),output=str(config.output))));return 0
        from .workflows.fast_screening import execute,reuse_analysis
        if getattr(args,'from_run',None):result=reuse_analysis(config,args.from_run,args.command)
        else:result=execute(config,args.command)
        print(str(result));return 0
    except Exception as exc:print('PathPocket: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
