"""Presentation helper run with installed RDKit. Coordinates only on a SMILES copy."""
import json,sys,hashlib,os
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Draw
def main(index_path,output):
    data=json.loads(Path(index_path).read_text(encoding='utf-8'));out=Path(output);out.mkdir(parents=True,exist_ok=True);audit=[]
    for row in data['rows']:
        smiles=row.get('smiles','');mol=Chem.MolFromSmiles(smiles) if smiles else None
        entry=dict(molecule_id=row['molecule_id'],target_id=row['target_id'],smiles=smiles,thumbnail=row['_thumb']+'.svg',rendered=mol is not None)
        if mol is not None:
            # MolToImage/MolDraw creates a depiction on a new SMILES molecule, never on a source SDF.
            drawer=Draw.MolDraw2DSVG(300,220);drawer.DrawMolecule(mol);drawer.FinishDrawing();(out/entry['thumbnail']).write_text(drawer.GetDrawingText(),encoding='utf-8')
        audit.append(entry)
    (out/'thumbnail_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    # Relabel existing source CSV values only: no fit, descriptors, clustering or QC.
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt,font_manager
    fonts=[Path(__file__).resolve().parents[2]/'assets/NotoSansCJK-Regular.ttc',Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),Path('/mnt/c/Windows/Fonts/msyh.ttc')]
    for path in fonts:
        if path.exists():font_manager.fontManager.addfont(str(path));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(path)).get_name();break
    plot_dir=out.parent/'figures';plot_dir.mkdir(exist_ok=True);plot_audit=[]
    for job in data.get('plots',[]):
        values=job['values']
        if not values:continue
        name=job['name'];fields=values[0]
        for lang in ['zh','en']:
            fig,ax=plt.subplots(figsize=(7.5,4.0),layout='constrained');ax.set_title(job['titles'][lang]);labels=[r.get('target_id',r.get('region_family_id',''))+' / '+r.get('state_id','') for r in values]
            if 'PC1' in fields and 'PC2' in fields:
                for state in dict.fromkeys(r['state_id'] for r in values):
                    subset=[r for r in values if r['state_id']==state];ax.scatter([float(r['PC1']) for r in subset],[float(r['PC2']) for r in subset],label=state,s=28)
                ax.set_xlabel('PC1');ax.set_ylabel('PC2');ax.legend()
            elif 'median' in fields:
                for i,r in enumerate(values):ax.vlines(i,float(r['q25']),float(r['q75']),color='#267d8b',linewidth=2);ax.scatter(i,float(r['median']),color='#267d8b')
                ax.set_xticks(range(len(values)),labels,rotation=20);ax.set_ylabel(values[0].get('property',''))
            else:
                key={'region_occurrence':'occurrence','generation_unique':'unique','generation_valid':'valid','predicted_ED':'predicted_ED_volume','normalized_Q':'median_Q_normalized'}.get(name)
                if not key or key not in fields:plt.close(fig);continue
                valid=[(label,r[key]) for label,r in zip(labels,values) if r.get(key) not in ['',None,'nan']]
                ax.bar([v[0] for v in valid],[float(v[1]) for v in valid],color='#267d8b');ax.tick_params(axis='x',rotation=20)
            ax.spines[['top','right']].set_visible(False);path=plot_dir/(name+'_'+lang+'.png');fig.savefig(path,dpi=160);plt.close(fig)
            plot_audit.append(dict(file=path.name,source=job['source'],source_values_unchanged=True,statistical_recomputation=False))
    (plot_dir/'plot_audit.json').write_text(json.dumps(plot_audit,indent=2),encoding='utf-8')
if __name__=='__main__':main(*sys.argv[1:])
