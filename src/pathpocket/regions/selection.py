def select_families(families,max_families,include_comparator=True):
    if not families:raise ValueError('No candidate regions discovered')
    result=[]
    for f in families:
        o=list(f['state_occurrence'].values());s=f['matching_stability']
        stable=min(o)>=.5 and max(o)-min(o)<=.3 and s is not None and s>=.7
        f['strict_state_stable_control']=stable
        f['role']='stable_comparator' if stable else ('emergent' if o[0]<=.2 and max(o[1:] or o)-o[0]>=.3 else 'persistent_remodeling_comparator')
    emergent=sorted([f for f in families if f['role']=='emergent'],key=lambda f:(-max(f['state_occurrence'].values()),f['region_family_id']))
    if emergent:result.append(emergent[0])
    if include_comparator:
        candidates=sorted([f for f in families if f not in result and f['role']!='emergent'],key=lambda f:(not f['strict_state_stable_control'],-min(f['state_occurrence'].values()),-sum(f['state_occurrence'].values()),f['region_family_id']))
        if candidates and len(result)<max_families:result.append(candidates[0])
    rest=sorted([f for f in families if f not in result],key=lambda f:(-sum(f['state_occurrence'].values()),f['region_family_id']))
    return (result+rest)[:max_families]
