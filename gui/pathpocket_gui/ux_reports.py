"""Independent bilingual presentation reports from immutable stored values."""
import html,json,os,base64
from urllib.parse import quote
from pathlib import Path
from .ux_i18n import tr,display,limitations,figure_title
from .ux_results import FIELDS
from .ux_export import friendly,write_molecules
def esc(v):return html.escape(str(v),quote=True)
def portable_href(path,directory):
    path=Path(path).resolve();directory=Path(directory).resolve()
    if not path.exists():return None
    return quote(os.path.relpath(path,directory).replace(os.sep,'/'),safe='/:')
def reports(index,directory):
    directory=Path(directory);out=[]
    selected_dir=directory/'molecules';molecule_index=write_molecules(index,selected_dir)
    for lang in ['zh','en']:
        t=lambda k:tr(k,lang)
        def link(path,key):
            href=portable_href(path,directory)
            return '<a href="'+esc(href)+'">'+esc(t(key))+'</a>' if href else '<span>'+esc(t(key))+': '+esc(t('missing'))+'</span>'
        cards=[];table=[]
        for row in index.rows:
            svg=directory/'thumbnails'/(row['_thumb']+'.svg')
            picture='<img alt="'+esc(row['molecule_id'])+'" src="data:image/svg+xml;base64,'+base64.b64encode(svg.read_bytes()).decode()+'">' if svg.exists() else '<p>NA</p>'
            badge='physical_compatible' if str(row.get('physical_compatible')).lower()=='true' else 'clash' if str(row.get('protein_clash')).lower()=='true' or str(row.get('internal_clash')).lower()=='true' else 'qc'
            values=' · '.join(esc(t(k))+': '+esc(display(row.get(k),lang)) for k in ['MW','cLogP','TPSA','Q_total_normalized','SA','QED'])
            cards.append('<article>'+picture+'<h3>'+esc(row['molecule_id'])+'</h3><p>'+esc(row['target_id'])+' / '+esc(row['region_family_id'])+' / '+esc(row['state_id'])+'</p><b>'+esc(t(badge))+'</b><p>'+values+'</p><code>'+esc(row.get('smiles','NA'))+'</code><p>'+link(selected_dir/friendly(index,row),'export_sdf')+' · '+link(row['_raw_sdf'],'raw_sdf')+' · '+link(row['_clean_sdf'],'clean_sdf')+' · '+link(row['_csv'],'source_csv')+'</p></article>')
            table.append('<tr>'+''.join('<td>'+esc(display(row.get(k),lang))+'</td>' for k in FIELDS)+'</tr>')
        summary=index.summary;metrics=summary.get('key_metrics',{})
        overview=''.join('<p><b>'+esc(t(k))+':</b> '+esc(v)+'</p>' for k,v in [('project',summary.get('project','NA')),('status',t('complete') if summary.get('status')=='COMPLETE' else summary.get('status','NA')),('run_folder',index.run),('generated',metrics.get('generated','NA')),('valid_unique',metrics.get('valid_unique_within_targets','NA')),('physical_compatible',metrics.get('physical_compatible_unique','NA'))])
        page='<!doctype html><html lang="'+('zh-CN' if lang=='zh' else 'en')+'"><meta charset="utf-8"><title>'+t('report_title')+'</title><style>body{font:15px system-ui;margin:28px;color:#17333b;background:#f5f8fa}h1,h2{color:#246b76}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px}article{background:white;padding:16px;border:1px solid #ccdce1;border-radius:8px;overflow-wrap:anywhere}img{max-width:100%}td,th{padding:8px;border-bottom:1px solid #ccdce1;white-space:nowrap}.scroll{overflow:auto}a{color:#176d80}code{overflow-wrap:anywhere}</style><body><h1>'+t('report_title')+'</h1><p>'+t('language_note')+'</p><p>'+t('scope')+'</p><h2>'+t('overview')+'</h2>'+overview+'<h2>'+t('generated')+'</h2><p>'+t('no_ranking')+'</p><div class="gallery">'+''.join(cards)+'</div><h2>'+t('table')+'</h2><div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(t(k))+'</th>' for k in FIELDS)+'</tr></thead><tbody>'+''.join(table)+'</tbody></table></div><h2>'+t('files')+'</h2>'+link(index.run/'artifacts.json','files')+' · '+link(index.run/'07_ANALYSIS/molecules.csv','source_csv')+'<p>'+t('pose_scope')+'</p><details><summary>'+t('advanced')+'</summary><pre>'+esc(json.dumps(index.source_hashes,indent=2))+'</pre></details></body></html>'
        figures=[]
        for f in index.figures:
            plot=directory/'figures'/(f['name']+'_'+lang+'.png')
            if plot.exists():figures.append('<section><h3>'+esc(figure_title(f['name'],lang))+'</h3><p>'+esc(tr('contains',lang,n=len(index.figure_members(f)) or 'NA'))+'</p><img src="data:image/png;base64,'+base64.b64encode(plot.read_bytes()).decode()+'"><p>'+link(index.run/'08_REPORT'/f['source'],'source_csv')+'</p></section>')
        page=page.replace('</body>','<h2>'+t('profile' if len(index.targets)<=1 else 'comparison')+'</h2>'+''.join(figures)+'<h2>'+t('warnings')+'</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in limitations(summary,lang))+'</ul></body>')
        path=directory/('report_'+lang+'.html');path.write_text(page,encoding='utf-8');out.append(path)
    (directory/'presentation_manifest.json').write_text(json.dumps(dict(source_run=str(index.run),read_only=True,scientific_recomputation=False,source_sha256=index.source_hashes,outputs=[p.name for p in out],molecule_index=molecule_index),indent=2),encoding='utf-8')
    return out
