"""Legitimate no-target output tables. No descriptors or molecular figures fabricated."""
from pathpocket.protein.normalization import csv_table

def empty_analysis(out):
    tables={
        'molecules':['molecule_id','target_id','region_family_id','state_id','valid','unique'],
        'generation_summary':['target_id','region_family_id','state_id','requested','generated','valid','unique','physical_compatible','actual_steps','predicted_ED_volume','median_Q_normalized'],
        'diversity':['target_id','region_family_id','state_id','unique','cluster_count','scaffold_count','within_state_diversity'],
        'property_summary':['target_id','region_family_id','state_id','property','n','median','q25','q75'],
        'state_comparison':['region_family_id','state_a','state_b','n_a','n_b'],
        'joint_embedding':['molecule_id','region_family_id','state_id','PC1','PC2'],
        'cluster_assignments':['molecule_id','target_id','cluster_id','cluster_size'],
        'scaffold_frequency':['target_id','region_family_id','state_id','scaffold','count']}
    for name,columns in tables.items():csv_table(out/(name+'.csv'),[],columns)
    return dict(diversity=[],properties=[],comparisons=[],embedding=[],result_class='NO_TARGETS',analysis_status='NOT_APPLICABLE')
