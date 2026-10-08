"""Descriptive workflow plots; no inferential tests or biological replicate claims."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def render(out,families,summaries,analysis,states,dpi=600):
    out=Path(out);out.mkdir(exist_ok=False);figures=[]
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':9,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    def save(fig,name,source,caption):
        fig.tight_layout();fig.canvas.draw()
        fig.savefig(out/(name+'.png'),dpi=dpi,bbox_inches='tight')
        fig.savefig(out/(name+'.svg'),bbox_inches='tight')
        fig.savefig(out/(name+'.pdf'),bbox_inches='tight')
        pd.DataFrame(source).to_csv(out/(name+'.csv'),index=False)
        (out/(name+'.alignment.json')).write_text(json.dumps({'status':'NOT_APPLICABLE','reason':'Single quantitative axes; colorbar is not a comparable panel'}))
        figures.append(dict(name=name,path='figures/'+name+'.png',svg='figures/'+name+'.svg',source='figures/'+name+'.csv',caption=caption));plt.close(fig)
    def heat(records,name,value,title):
        d=pd.DataFrame(records)
        if d.empty:return
        pivot=d.pivot(index='region_family_id',columns='state_id',values=value).reindex(columns=list(states));values=pivot.to_numpy(float);finite=np.isfinite(values)
        upper=1 if value in ['occurrence','median_Q_normalized'] or not finite.any() else max(1,float(np.nanmax(values)))
        fig,ax=plt.subplots(figsize=(6,3.6));im=ax.imshow(values,aspect='auto',cmap='viridis',vmin=0,vmax=upper)
        ax.set_xticks(range(len(pivot.columns)),[states[s]['label'] for s in pivot.columns]);ax.set_yticks(range(len(pivot.index)),pivot.index);ax.set_title(title,pad=12)
        if finite.any():fig.colorbar(im,ax=ax,fraction=.035,pad=.04)
        for i,j in np.ndindex(values.shape):
            v=values[i,j];label='NA' if not np.isfinite(v) else f'{v:.0f}' if value in ['valid','unique'] else f'{v:.3g}'
            ax.text(j,i,label,ha='center',va='center',fontsize=9,color='white' if np.isfinite(v) and v/upper<.45 else 'black')
        save(fig,name,d,title+'; one target per family/state, descriptive values, no biological replicates. NA means unavailable, not zero.')
    occurrence=[dict(region_family_id=f['region_family_id'],state_id=s,occurrence=v) for f in families for s,v in f['state_occurrence'].items()]
    heat(occurrence,'region_occurrence','occurrence','Detected region occurrence (fraction)')
    for name,key,title in [('generation_unique','unique','Valid unique molecules (count)'),('generation_valid','valid','Valid molecules (count)'),('predicted_ED','predicted_ED_volume','Predicted ED volume ($\AA^3$)'),('normalized_Q','median_Q_normalized','Median normalized Q (unitless)')]:heat(summaries,name,key,title)
    prop=pd.DataFrame(analysis['properties']);embedding=pd.DataFrame(analysis['embedding'])
    for family in sorted(embedding.region_family_id.unique()) if not embedding.empty else []:
        d=embedding[embedding.region_family_id==family];fig,ax=plt.subplots(figsize=(6,4))
        for state in states:
            sub=d[d.state_id==state];ax.scatter(sub.PC1,sub.PC2,s=9,alpha=.5,label=f'{states[state]["label"]} (n={len(sub)})')
        ax.set(xlabel='Joint fingerprint PC1',ylabel='Joint fingerprint PC2',title=f'{family}: variance {d.explained_variance.iloc[0]:.1%}');ax.legend(loc='upper left',bbox_to_anchor=(1,1),fontsize=8);save(fig,'embedding_'+family,d,'Joint family PCA of all valid unique ECFP4 fingerprints; one common fit across states. Projection is illustrative.')
        for property_name in ['MW','cLogP','TPSA']:
            sub=prop[(prop.region_family_id==family)&(prop.property==property_name)];fig,ax=plt.subplots(figsize=(5.5,3.5))
            sub=sub.set_index('state_id').reindex(list(states));x=np.arange(len(sub));ax.errorbar(x,sub['median'],yerr=[sub['median']-sub.q25,sub.q75-sub['median']],fmt='o',capsize=4,color='#35688d');ax.set_xticks(x,[states[s]['label'] for s in sub.index]);ax.set(ylabel=property_name+(' (Da)' if property_name=='MW' else ' ($\AA^2$)' if property_name=='TPSA' else ''),title=f'{family}: median and IQR');ax.margins(x=.2);save(fig,'descriptor_'+property_name+'_'+family,sub.reset_index(),'Median and interquartile range of generated valid unique molecules; not a biological confidence interval.')
    pairs=analysis['comparisons']
    if pairs:
        d=pd.DataFrame(pairs);fig,ax=plt.subplots(figsize=(7,max(3,len(d)*.32)));ax.barh(np.arange(len(d)),d.scaffold_jaccard,color='#35688d');ax.set_yticks(np.arange(len(d)),[f'{r.region_family_id}: {r.state_a}/{r.state_b}' for r in d.itertuples()],fontsize=8);ax.set(xlim=(0,1),xlabel='Scaffold Jaccard (including ACYCLIC)',title='Cross-state scaffold overlap');save(fig,'scaffold_overlap',d,'Set overlap; sampling depth affects observed scaffold support.')
    return figures
