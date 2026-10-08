import os
import yaml
from pathpocket.core.paths import native_path
from .schema import validate_data

class UniqueLoader(yaml.SafeLoader): pass
def mapping(loader,node,deep=False):
    result={}
    for key,value in node.value:
        k=loader.construct_object(key,deep=deep)
        if k in result: raise ValueError(f'Duplicate YAML key/state ID: {k}')
        result[k]=loader.construct_object(value,deep=deep)
    return result
UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,mapping)

def load_config(path,workspace=None):
    path=native_path(path)
    workspace=workspace or os.environ.get('PATHPOCKET_WORKSPACE')
    if not workspace: raise ValueError('Set PATHPOCKET_WORKSPACE to the authorized canonical workspace')
    return validate_data(yaml.load(path.read_text(encoding='utf-8-sig'),Loader=UniqueLoader),path,workspace)
