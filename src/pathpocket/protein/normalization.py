"""Auditable canonical IDs across observed chains; raw PDB coordinates stay intact."""
import csv,json
from dataclasses import asdict
from pathlib import Path
from .structure import atoms
from .residue_mapping import CanonicalResidueID,MappingPolicy,MappingError,extract_chains,sequence_mapping
from .chain_mapping import assign_chains

def csv_table(path,rows,columns):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(rows)

def normalize(receptors,out,policy=MappingPolicy()):
    out=Path(out);reference=receptors[0];ref_id=reference['receptor_id'];chains={};assignments={};chain_rows=[];sequence_rows=[]
    summary=dict(status='PASS',mapping_mode='identity',reference_state=reference['state_id'],reference_receptor_id=ref_id,policy=asdict(policy),warnings=[],chain_mappings=[])
    try:
        for r in receptors:
            rid=r['receptor_id'];chains[rid]=extract_chains(atoms(r['path']))
            for chain,residues in chains[rid].items():sequence_rows.append(dict(receptor_id=rid,state_id=r['state_id'],chain_id=chain,observed_sequence=''.join(x['aa'] for x in residues),observed_residues=len(residues),raw_ids=json.dumps([x['raw_id'] for x in residues])))
        refs=chains[ref_id]
        for r in receptors:
            rid=r['receptor_id'];assignments[rid]=assign_chains(refs,chains[rid],policy,rid==ref_id)
            for a in assignments[rid]:
                c=a.residue_mapping.confidence
                chain_rows.append(dict(receptor_id=rid,state_id=r['state_id'],reference_state=reference['state_id'],reference_chain=a.reference_chain,target_chain=a.target_chain,mapping_mode=a.residue_mapping.mode,**asdict(c),score=c.score,status=a.status,ambiguity=a.ambiguity,mapped_residue_count=len(chains[rid][a.target_chain])))
        # Each insertion slot has a sequence-derived local scaffold. No synthetic atoms.
        maps={r['receptor_id']:{} for r in receptors};canonical_by_chain={}
        for chain_number,(ref_chain,ref_res) in enumerate(refs.items(),1):
            cid=f'REF_{chain_number:03d}';slot_scaffolds={};slot_maps={}
            for anchor in range(len(ref_res)+1):
                chunks=[]
                for rid,items in assignments.items():
                    a=next(x for x in items if x.reference_chain==ref_chain);indices=a.residue_mapping.insertions.get(anchor,[])
                    if indices:chunks.append((rid,a,indices,[chains[rid][a.target_chain][j] for j in indices]))
                if not chunks:continue
                scaffold=max((x[3] for x in chunks),key=lambda x:(len(x),''.join(y['aa'] for y in x)))
                slot_scaffolds[anchor]=scaffold
                for rid,a,indices,chunk in chunks:
                    if [x['aa'] for x in chunk]==[x['aa'] for x in scaffold]:positions=dict(enumerate(range(len(chunk))))
                    else:
                        local=sequence_mapping(scaffold,chunk)
                        if local.alignment_ambiguous or local.confidence.identity!=1 or local.confidence.coverage_target!=1:
                            raise MappingError('AMBIGUOUS','Insertion-slot correspondence is not uniquely supported by observed sequences')
                        positions=local.target_to_reference
                    for local_j,scaffold_i in positions.items():slot_maps[rid,indices[local_j]]=anchor,scaffold_i
            ordinal={};canonicals=[]
            for anchor in range(len(ref_res)+1):
                for j,res in enumerate(slot_scaffolds.get(anchor,[])):
                    key=CanonicalResidueID(cid,len(canonicals)+1,res['resname']).serialize();ordinal['insert',anchor,j]=key;canonicals.append(key)
                if anchor<len(ref_res):
                    key=CanonicalResidueID(cid,len(canonicals)+1,ref_res[anchor]['resname']).serialize();ordinal['reference',anchor]=key;canonicals.append(key)
            canonical_by_chain[ref_chain]=canonicals
            for rid,items in assignments.items():
                a=next(x for x in items if x.reference_chain==ref_chain);target=chains[rid][a.target_chain]
                for j,res in enumerate(target):
                    if j in a.residue_mapping.target_to_reference:key=ordinal['reference',a.residue_mapping.target_to_reference[j]]
                    else:
                        anchor,k=slot_maps[rid,j];key=ordinal['insert',anchor,k]
                    maps[rid][res['raw_id']]=key
        residue_rows=[]
        for r in receptors:
            rid=r['receptor_id']
            for a in assignments[rid]:
                present={}
                for raw in chains[rid][a.target_chain]:
                    key=maps[rid][raw['raw_id']];assert key not in present;present[key]=raw
                for key in canonical_by_chain[a.reference_chain]:
                    raw=present.get(key);canonical=CanonicalResidueID.parse(key)
                    residue_rows.append(dict(receptor_id=rid,state_id=r['state_id'],reference_chain=a.reference_chain,target_chain=a.target_chain,raw_residue_id=raw['raw_id'] if raw else '',raw_residue_name=raw['resname'] if raw else '',canonical_residue_id=key,**asdict(canonical),status='MAPPED' if raw else 'GAP',coordinates_present=bool(raw)))
        summary.update(mapping_mode='identity' if all(x['mapping_mode']=='identity' for x in chain_rows) else 'sequence',mapped_chains=len(chain_rows),mapped_residue_count=sum(len(x) for x in maps.values()),gap_count=sum(x['status']=='GAP' for x in residue_rows),chain_mappings=chain_rows)
        if summary['gap_count']:summary['warnings'].append('Observed-residue gaps retained; no coordinates modeled')
        csv_table(out/'residue_mapping.csv',residue_rows,list(residue_rows[0]))
        (out/'residue_identity_maps.json').write_text(json.dumps(maps,indent=2))
        return maps,summary
    except MappingError as exc:
        summary.update(status=exc.status.value,error=str(exc),candidate_correspondences=exc.details)
        csv_table(out/'residue_mapping.csv',[],['receptor_id','state_id','reference_chain','target_chain','raw_residue_id','canonical_residue_id','status','coordinates_present'])
        chain_rows.append(dict(receptor_id=rid if 'rid' in locals() else '',state_id=r['state_id'],reference_state=reference['state_id'],status=exc.status.value,ambiguity=exc.status.value=='AMBIGUOUS',mapping_mode='unresolved'))
        summary['chain_mappings']=chain_rows
        raise
    finally:
        csv_table(out/'chain_sequence_table.csv',sequence_rows,['receptor_id','state_id','chain_id','observed_sequence','observed_residues','raw_ids'])
        csv_table(out/'chain_mapping.csv',chain_rows,['receptor_id','state_id','reference_state','reference_chain','target_chain','mapping_mode','identity','coverage_ref','coverage_target','score','gap_count','mismatch_count','mapped_residue_count','status','ambiguity'])
        (out/'mapping_summary.json').write_text(json.dumps(summary,indent=2))

def canonical_records(records,mapping):
    return [dict(a,residue=mapping[a['residue']]) for a in records]
