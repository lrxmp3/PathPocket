import itertools
import numpy as np
import pandas as pd
from rdkit import Chem,DataStructs
from rdkit.Chem import AllChem
from rdkit.ML.Cluster import Butina
from scipy.stats import wasserstein_distance
from sklearn.decomposition import PCA

PROPERTIES=['MW','cLogP','TPSA','HBD','HBA','rotatable_bonds','ring_count','aromatic_ring_count','fractionCSP3','formal_charge','SA','QED','Q_total_normalized','ED_coverage']
def fingerprint(m):return AllChem.GetMorganFingerprintAsBitVect(Chem.RemoveHs(m),2,nBits=2048,useChirality=False)
def profile(master,molecules,out):
    good=master[master.valid & master.unique].copy();fps={k:fingerprint(v) for k,v in molecules.items()};div=[];props=[];pairs=[];embeddings=[];assignments=[]
    fp_ids=sorted(fps)
    np.savez_compressed(out/'fingerprints.npz',molecule_ids=np.array(fp_ids,dtype=str),bits=np.array([list(fps[k]) for k in fp_ids],dtype=np.uint8).reshape((-1,2048)))
    for target,d in good.groupby('target_id'):
        ids=list(d.molecule_id);flat=[]
        for i in range(1,len(ids)):flat.extend(1-np.array(DataStructs.BulkTanimotoSimilarity(fps[ids[i]],[fps[k] for k in ids[:i]])))
        clusters=Butina.ClusterData(flat,len(ids),.4,isDistData=True,reordering=True)
        for cluster_number,indices in enumerate(clusters,1):
            for index in indices:assignments.append(dict(molecule_id=ids[index],target_id=target,cluster_id=target+f'_C{cluster_number:04d}',cluster_size=len(indices)))
        div.append(dict(target_id=target,region_family_id=d.iloc[0].region_family_id,state_id=d.iloc[0].state_id,unique=len(ids),cluster_count=len(clusters),scaffold_count=d.scaffold.nunique(),within_state_diversity=float(np.mean(flat)) if flat else None))
        for p in PROPERTIES:
            props.append(dict(target_id=target,region_family_id=d.iloc[0].region_family_id,state_id=d.iloc[0].state_id,property=p,n=len(d),median=float(d[p].median()),q25=float(d[p].quantile(.25)),q75=float(d[p].quantile(.75))))
    for family,d in good.groupby('region_family_id'):
        ids=list(d.molecule_id);matrix=np.array([list(fps[k]) for k in ids]);components=min(2,len(ids),matrix.shape[1]);pca=PCA(n_components=components,svd_solver='full');xy=pca.fit_transform(matrix)
        for i,row in enumerate(d.itertuples()):embeddings.append(dict(molecule_id=row.molecule_id,region_family_id=family,state_id=row.state_id,PC1=float(xy[i,0]),PC2=float(xy[i,1]) if components>1 else 0,explained_variance=float(np.nansum(pca.explained_variance_ratio_))))
        for a,b in itertools.combinations(sorted(d.state_id.unique()),2):
            da=d[d.state_id==a];db=d[d.state_id==b];sim=np.array([DataStructs.BulkTanimotoSimilarity(fps[k],[fps[j] for j in db.molecule_id]) for k in da.molecule_id]);sa=set(da.scaffold);sb=set(db.scaffold)
            rec=dict(region_family_id=family,state_a=a,state_b=b,n_a=len(da),n_b=len(db),nearest_Tanimoto_a_to_b=float(sim.max(1).mean()),nearest_Tanimoto_b_to_a=float(sim.max(0).mean()),scaffold_jaccard=len(sa&sb)/len(sa|sb))
            for p in PROPERTIES:rec['wasserstein_'+p]=float(wasserstein_distance(da[p].dropna(),db[p].dropna())) if da[p].notna().any() and db[p].notna().any() else None
            pairs.append(rec)
    columns={'diversity':['target_id','region_family_id','state_id','unique','cluster_count','scaffold_count','within_state_diversity'],'property_summary':['target_id','region_family_id','state_id','property','n','median','q25','q75'],'state_comparison':['region_family_id','state_a','state_b','n_a','n_b','nearest_Tanimoto_a_to_b','nearest_Tanimoto_b_to_a','scaffold_jaccard']+['wasserstein_'+p for p in PROPERTIES],'joint_embedding':['molecule_id','region_family_id','state_id','PC1','PC2','explained_variance'],'cluster_assignments':['molecule_id','target_id','cluster_id','cluster_size']}
    for name,records in [('diversity',div),('property_summary',props),('state_comparison',pairs),('joint_embedding',embeddings),('cluster_assignments',assignments)]:pd.DataFrame(records,columns=columns[name]).to_csv(out/(name+'.csv'),index=False)
    if not good.empty:good.groupby(['target_id','region_family_id','state_id','scaffold']).size().rename('count').reset_index().to_csv(out/'scaffold_frequency.csv',index=False)
    else:pd.DataFrame(columns=['target_id','region_family_id','state_id','scaffold','count']).to_csv(out/'scaffold_frequency.csv',index=False)
    return dict(diversity=div,properties=props,comparisons=pairs,embedding=embeddings)
