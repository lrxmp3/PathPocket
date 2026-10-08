"""Deterministic engineering fixtures; never representations of a measured fibril."""
import numpy as np
from pathlib import Path
from pathpocket.protein.residue_mapping import AA

SEQ='ACDEFGHIKLMNPQRSTVWY'
def stack(path,n=7,spacing=None,ring=False,lanes=False,rename=False,reorder=False,rotation=None,translation=None):
    inverse={v:k for k,v in AA.items()};zs=np.arange(n)*4.8 if spacing is None else np.r_[0,np.cumsum(spacing)];blocks=[]
    labels=list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
    count=n*(2 if lanes else 1);ids=labels[:count] if not rename else list(reversed(labels))[:count]
    for copy in range(count):
        j=copy%n;lane=copy//n
        shift=np.array([0.,0.,zs[j]]) if not ring else np.array([12*np.cos(2*np.pi*j/n),12*np.sin(2*np.pi*j/n),0.])
        if lanes:shift+=np.array([8*lane,0.,0.])
        block=[]
        for k,aa in enumerate(SEQ):
            # A folded planar engineering peptide, deliberately not a physical structure claim.
            ca=np.array([3.4*(k if k<10 else 18-k),5.*(k>=10)+.6*(k%2),.15*np.sin(k)])
            for atom,delta,element in [('N',[-1.1,-.1,0],'N'),('CA',[0,0,0],'C'),('C',[1.1,.1,0],'C'),('O',[1.6,.9,0],'O'),('CB',[0,1.4,.8],'C')]:
                xyz=ca+delta+shift
                if rotation is not None:xyz=xyz@rotation
                if translation is not None:xyz+=translation
                block.append((ids[copy],k+1,inverse[aa],atom,element,xyz))
        if reorder:block=block[::-1]
        blocks.append(block)
    if reorder:blocks=blocks[::2][::-1]+blocks[1::2]
    lines=[]
    for block in blocks:
        for c,p,res,atom,e,xyz in block:lines.append(f'ATOM  {len(lines)+1:5d} {atom:>4s} {res:3s} {c}{p:4d}    '+''.join(f'{v:8.3f}' for v in xyz)+f'  1.00 20.00          {e:>2s}  ')
    Path(path).write_text('\n'.join(lines)+'\nEND\n');return Path(path)
