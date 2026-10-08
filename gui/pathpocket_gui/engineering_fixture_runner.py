"""Isolated entry point for the trusted built-in zero-target engineering fixture."""
import hashlib,importlib.util,json,sys
from pathlib import Path

FIXTURE_ID='builtin_no_targets_v1'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def install_packaged_transport(repo):
    """Load the release path transport for this directly-launched helper."""
    transport=Path(repo)/'archive_transport.py'
    if not transport.is_file():return False
    spec=importlib.util.spec_from_file_location('pathpocket_archive_transport',transport)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.install(repo)
    return True

def verify(config_path,marker_path):
    import yaml
    config_path=Path(config_path).resolve();project=config_path.parent;marker_path=Path(marker_path).resolve()
    if marker_path!=project/'pathpocket_engineering_fixture.json':raise ValueError('Fixture marker is not inside the project')
    marker=json.loads(marker_path.read_text(encoding='utf-8'));data=yaml.safe_load(config_path.read_text(encoding='utf-8-sig'))
    inputs={str(p.relative_to(project)):digest(p) for p in sorted((project/'inputs').rglob('*')) if p.is_file()}
    checks=[marker.get('schema_version')==1,marker.get('fixture_id')==FIXTURE_ID,
        marker.get('trusted_builtin') is True,marker.get('source')=='bundled:examples/fixtures/DEMO_NO_TARGETS',
        marker.get('project_path')==str(project),marker.get('project_name')==data['project']['name'],
        marker.get('project_config_sha256')==digest(config_path),marker.get('input_sha256')==inputs]
    if not all(checks):raise ValueError('Engineering fixture identity check failed; refusing forced-empty selection')
    return marker

def main(argv):
    if len(argv)!=3:raise ValueError('Expected project.yml and engineering fixture marker')
    repo=Path(__file__).resolve().parents[2]
    install_packaged_transport(repo)
    development_source=(repo/'src').resolve();packaged_source=(repo/'payload/v106_no_targets_hf2_overlay').resolve()
    source=packaged_source if packaged_source.is_dir() else development_source
    if not source.is_dir():raise FileNotFoundError('v1.0.6 NO_TARGETS HF2 workflow overlay is missing')
    marker=verify(argv[1],argv[2])
    from pathpocket.config.loader import load_config
    import pathpocket.core.provenance as provenance
    config=load_config(Path(argv[1]));engine=Path(config.data['runtime']['ed2mol_root']).resolve();release=engine.parent.parent/'release_manifest.json'
    original_git_commit=provenance.git_commit
    def portable_git_commit(path):
        if Path(path).resolve()==engine and release.is_file():return json.loads(release.read_text())['engine_commit']
        return original_git_commit(path)
    provenance.git_commit=portable_git_commit
    spec=importlib.util.spec_from_file_location('pathpocket.workflows.v106_no_targets_hf2',source/'pathpocket/workflows/fast_screening.py')
    workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
    run=workflow.execute(config,engineering_fixture={'fixture_id':marker['fixture_id'],'source':marker['source'],
        'semantics':marker['semantics'],'marker_sha256':digest(argv[2]),'selection_policy':'FORCE_EMPTY_AT_TARGET_SELECTION'})
    print(run);return 0

if __name__=='__main__':
    try:raise SystemExit(main(sys.argv))
    except Exception as exc:
        print('PathPocket engineering fixture failed: '+str(exc),file=sys.stderr);raise SystemExit(1)
