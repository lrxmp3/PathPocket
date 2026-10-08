"""Native Qt interactive 3D coordinate projection; no chemical computation."""
import math,json
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QPainter,QPen,QColor
from PySide6.QtWidgets import QWidget,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QPlainTextEdit,QSplitter,QCheckBox,QToolTip
PALETTE=['#6673bd','#299ab0','#258654','#d7852f','#bc659f']
class CoordinateView(QWidget):
 def __init__(self,data,parent=None):
  super().__init__(parent);self.data=data;self.yaw=.35;self.pitch=-.5;self.pan=[0,0];self.last=None;self.show_lining=True;self.show_ligand=True;self.setMinimumSize(480,400);self.setMouseTracking(True);self.fit(False)
 def fit(self,local=False):
  points=([a['xyz'] for a in self.data['atoms'] if a['lining']]+[a['xyz'] for a in self.data['ligand']]+[self.data['center']]) if local else [a['xyz'] for a in self.data['atoms']]+[self.data['center']]
  self.origin=[sum(p[i] for p in points)/len(points) for i in range(3)];self.radius=max(8,max(math.dist(p,self.origin) for p in points));self.zoom=1.;self.pan=[0,0];self.update()
 def project(self,xyz):
  x,y,z=[xyz[i]-self.origin[i] for i in range(3)];x,z=x*math.cos(self.yaw)+z*math.sin(self.yaw),-x*math.sin(self.yaw)+z*math.cos(self.yaw);y,z=y*math.cos(self.pitch)-z*math.sin(self.pitch),y*math.sin(self.pitch)+z*math.cos(self.pitch);scale=min(self.width(),self.height())*.43/self.radius*self.zoom
  return QPointF(self.width()/2+x*scale+self.pan[0],self.height()/2-y*scale+self.pan[1]),z
 def paintEvent(self,e):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor('#f5f8fb'));self.hits=[];segments=[];prev={};chains=sorted({a['chain'] for a in self.data['atoms']})
  for a in self.data['atoms']:
   if a['name']!='CA':continue
   pt,z=self.project(a['xyz']);color=PALETTE[chains.index(a['chain'])%len(PALETTE)]
   if a['chain'] in prev:
    b,bpt,bz=prev[a['chain']]
    if math.dist(a['xyz'],b['xyz'])<5:segments.append(((z+bz)/2,bpt,pt,color))
   prev[a['chain']]=(a,pt,z);self.hits.append((pt,a['resname']+' '+a['canonical']))
  for z,a,b,c in sorted(segments,key=lambda x:x[0]):p.setPen(QPen(QColor(c),2.5));p.drawLine(a,b)
  if self.show_lining:
   for a in sorted([a for a in self.data['atoms'] if a['lining']],key=lambda a:self.project(a['xyz'])[1]):
    pt,z=self.project(a['xyz']);p.setPen(Qt.NoPen);p.setBrush(QColor('#d89a20'));p.drawEllipse(pt,2.3,2.3);self.hits.append((pt,a['resname']+' '+a['canonical']+' '+a['name']))
  if self.show_ligand:
   for a,b,order in self.data['bonds']:
    pa,za=self.project(self.data['ligand'][a]['xyz']);pb,zb=self.project(self.data['ligand'][b]['xyz']);p.setPen(QPen(QColor('#253648'),3.3));p.drawLine(pa,pb)
   for a in sorted(self.data['ligand'],key=lambda a:self.project(a['xyz'])[1]):
    pt,z=self.project(a['xyz']);p.setPen(QPen(QColor('white'),1));p.setBrush(QColor({'O':'#e44b51','N':'#347fe0','S':'#dcc138','F':'#73c786','Cl':'#55ae69'}.get(a['element'],'#37485c')));p.drawEllipse(pt,4.5,4.5)
  pt,z=self.project(self.data['center']);p.setPen(QPen(QColor('#d33191'),2));p.setBrush(Qt.NoBrush);p.drawEllipse(pt,9,9);p.drawLine(pt+QPointF(-15,0),pt+QPointF(15,0));p.drawLine(pt+QPointF(0,-15),pt+QPointF(0,15))
  y=23
  for i,c in enumerate(chains):
   offset=self.data['chains'].get(c);label=c+('  repeat '+format(offset,'+d') if offset is not None else '')
   p.setPen(QColor(PALETTE[i%len(PALETTE)]));p.drawText(16,y,label);y+=21
  p.end()
 def mousePressEvent(self,e):self.last=e.position()
 def mouseReleaseEvent(self,e):self.last=None
 def mouseMoveEvent(self,e):
  if self.last and e.buttons():
   delta=e.position()-self.last;self.last=e.position()
   if e.buttons() & Qt.RightButton:self.pan[0]+=delta.x();self.pan[1]+=delta.y()
   else:self.yaw+=delta.x()*.01;self.pitch+=delta.y()*.01
   self.update()
  else:
   hit=next((label for pt,label in getattr(self,'hits',[]) if (pt-e.position()).manhattanLength()<8),None)
   if hit:QToolTip.showText(e.globalPosition().toPoint(),hit,self)
 def wheelEvent(self,e):self.zoom=max(.1,min(20,self.zoom*math.exp(e.angleDelta().y()/1200)));self.update()

class StructureDialog(QDialog):
 def __init__(self,data,zh=True,parent=None,on_export=None):
  super().__init__(parent);self.data=data;self.setWindowTitle('结构定位' if zh else 'Structure Location Explorer');self.resize(1280,830);v=QVBoxLayout(self)
  tip=QLabel('结合区域形状、衬里残基与分子结构，探索后续识别基团或探针的设计方向。' if zh else 'Explore design directions using the region shape, lining residues and molecular structure.');tip.setWordWrap(True);tip.setStyleSheet('background:#e3eff3;padding:10px');v.addWidget(tip)
  if on_export:
   export=QPushButton('导出蛋白–配体复合物' if zh else 'Export Protein–Ligand Complex');export.setToolTip('导出当前蛋白与分子的三维组合结构，便于后续结构观察与研究。' if zh else 'Export the current protein–molecule structure for downstream visualization and research.');export.clicked.connect(on_export);v.addWidget(export);self.export_button=export
  advanced=QCheckBox('高级帮助' if zh else 'Advanced Help');boundary=QLabel('ED2Mol 生成构象不是已验证结合姿势；本视图与导出不执行 docking、最小化或质子化。' if zh else 'An ED2Mol-generated conformation is not a validated binding pose; viewing and export perform no docking, minimization or protonation.');boundary.setWordWrap(True);boundary.hide();advanced.toggled.connect(boundary.setVisible);v.addWidget(advanced);v.addWidget(boundary)
  split=QSplitter();v.addWidget(split,1);left=QWidget();lv=QVBoxLayout(left);self.canvas=CoordinateView(data);lv.addWidget(self.canvas,1);buttons=QHBoxLayout()
  for text,fn in [(('完整结构' if zh else 'Full structure'),lambda:self.canvas.fit(False)),(('聚焦区域' if zh else 'Focus region'),lambda:self.canvas.fit(True))]:
   b=QPushButton(text);b.clicked.connect(fn);buttons.addWidget(b)
  for text,attr in [(('区域衬里残基' if zh else 'Lining residues'),'show_lining'),(('生成分子' if zh else 'Generated molecule'),'show_ligand')]:
   b=QCheckBox(text);b.setChecked(True);b.toggled.connect(lambda val,k=attr:(setattr(self.canvas,k,val),self.canvas.update()));buttons.addWidget(b)
  lv.addLayout(buttons);lv.addWidget(QLabel('左键旋转 · 滚轮缩放 · 右键平移 · 悬停查看残基\n彩色线：Cα 骨架；金色点：已有衬里残基；粉色十字：target center' if zh else 'Drag to rotate · Wheel to zoom · Right-drag to pan · Hover for residue\nColored lines: Cα trace; gold: stored lining residues; magenta cross: target center'));split.addWidget(left)
  self.info=QPlainTextEdit();self.info.setReadOnly(True);self.info.setMinimumWidth(300);split.addWidget(self.info);split.setSizes([880,350])
  t=data['target'];m=data['molecule'] or {};metrics=data['metrics'];q=m.get('Q_total_normalized',metrics.get('median_Q_normalized','NA'))
  details=[(('目标' if zh else 'Target'),t['target_id']),(('区域家族' if zh else 'Region family'),t.get('region_family_id')),(('状态' if zh else 'State'),t.get('state_id')),(('fpocket 排名' if zh else 'fpocket rank'),data['rank'] if data['rank'] is not None else 'NA'),(('中心 (Å)' if zh else 'Center (Å)'),data['center']),(('重复单元偏移' if zh else 'Repeat offsets'),sorted(data['chains'].values())),(('分子' if zh else 'Molecule'),m.get('molecule_id','NA')),(('预测 ED 体积' if zh else 'Predicted ED volume'),metrics.get('predicted_ED_volume','NA')),('Qnorm' if m else 'Median Qnorm',q),(('物理兼容' if zh else 'Physical-compatible'),m.get('physical_compatible','NA')),(('衬里映射' if zh else 'Lining mapped'),str(len(data['matched_lining']))+'/'+str(len(data['lining_residues'])))]
  from .ux_plots import HELP
  molecule_properties=[(('文件' if zh else 'File'),data.get('friendly_filename','NA')),('SMILES',m.get('smiles','NA'))]+[(key,m.get(key,'NA')) for key in ['MW','cLogP','TPSA','SA','QED']]
  text='\n\n'.join(k+': '+str(val) for k,val in details+molecule_properties)
  text+='\n\n'+('衬里残基' if zh else 'Lining residues')+'\n'+'\n'.join(data['lining_residues'])
  self.info.setPlainText(text);self.info.setToolTip('\n'.join(key+': '+val[0 if zh else 1] for key,val in HELP.items() if key in ['Qnorm','physical_compatible','cLogP','TPSA','SA','QED']))
