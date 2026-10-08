"""Read stored plot coordinates/properties; render without fitting or metrics."""
import math
from pathlib import Path
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QPainter,QPen,QColor
from PySide6.QtWidgets import QWidget,QScrollArea
from .ux_results import rows,truth
HELP={
'PCA':('查看当前目标生成分子的化学空间分布。','Explore the chemical-space distribution of molecules generated for this target.'),
'MW':('查看生成分子的分子量分布。','View the molecular-weight distribution.'),
'cLogP':('查看分子疏水性及当前区域对应的化学性质范围。','Explore hydrophobicity and the chemical-property range for this region.'),
'TPSA':('查看分子极性表面积，辅助观察极性适配趋势。','Explore polar surface area and polarity trends.'),
'Qnorm':('比较当前目标内分子与预测电子密度的匹配程度。','Compare predicted electron-density fit within the current target.'),
'SA':('观察生成结构的合成复杂度趋势。','Explore synthetic-complexity trends.'),
'QED':('查看常用药物样性质指标的分布。','View the distribution of a common drug-likeness descriptor.'),
'physical_compatible':('快速标记明显几何冲突，便于优先查看候选结构。','Flag obvious geometric clashes to prioritize structural review.')}

class HorizontalPlots(QScrollArea):
 def wheelEvent(self,event):
  delta=event.angleDelta().x() or event.angleDelta().y();bar=self.horizontalScrollBar();bar.setValue(bar.value()-delta);event.accept()

def plot_data(index,tid,key):
 selected=[r for r in index.rows if r['target_id']==tid and truth(r.get('valid')) and truth(r.get('unique'))];points=[];ids=[]
 if key=='PCA':
  source=index.run/'07_ANALYSIS/joint_embedding.csv';lookup={}
  for r in rows(source):lookup.setdefault((r.get('molecule_id'),r.get('region_family_id'),r.get('state_id')),[]).append(r)
  for r in selected:
   found=lookup.get((r['molecule_id'],r['region_family_id'],r['state_id']),[])
   if len(found)!=1:continue
   try:x,y=float(found[0]['PC1']),float(found[0]['PC2'])
   except (KeyError,ValueError):continue
   if math.isfinite(x) and math.isfinite(y):points.append((x,y));ids.append(r['molecule_id'])
 else:
  source=index.run/'06_CHEMICAL_CHALLENGE'/tid/'molecule_qc.csv';column='Q_total_normalized' if key=='Qnorm' else key
  for r in selected:
   try:x=float(r[column])
   except (ValueError,KeyError,TypeError):continue
   if math.isfinite(x):points.append((x,0));ids.append(r['molecule_id'])
 return dict(key=key,points=points,molecule_ids=ids,source=str(source),target_id=tid)

class StoredPlot(QWidget):
 def __init__(self,parent=None):
  super().__init__(parent);self.data=None;self.zh=True;self.setMinimumHeight(220)
 def show_data(self,data,zh):self.data=data;self.zh=zh;self.update()
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor('white'));p.setPen(QColor('#254553'))
  if not self.data or not self.data['points']:p.drawText(self.rect(),Qt.AlignCenter,'暂无已存数据' if self.zh else 'No stored data');return
  pts=self.data['points'];key=self.data['key'];p.drawText(24,28,key+' · '+self.data['target_id']);p.drawText(24,50,('有效唯一分子：' if self.zh else 'Valid unique molecules: ')+str(len(pts)))
  left,right,top,bottom=72,self.width()-35,80,self.height()-55;xs=[v[0] for v in pts];ys=[v[1] for v in pts];xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
  # Extents only map stored values to pixels; no bins, statistics, PCA or descriptors.
  dx=(xmax-xmin) or 1;dy=(ymax-ymin) or 1
  p.setPen(QPen(QColor('#859ca5'),1));p.drawLine(left,bottom,right,bottom)
  if key=='PCA':p.drawLine(left,top,left,bottom)
  p.setPen(QColor('#254553'));p.drawText(left,bottom+22,format(xmin,'.5g'));p.drawText(right-60,bottom+22,format(xmax,'.5g'));p.drawText((left+right)//2,bottom+40,'PC1' if key=='PCA' else key)
  if key=='PCA':p.drawText(6,top,format(ymax,'.4g'));p.drawText(6,bottom,format(ymin,'.4g'));p.drawText(8,(top+bottom)//2,'PC2')
  else:p.drawText(left,top,('每点对应一个已生成分子' if self.zh else 'One point per generated molecule'))
  p.setBrush(QColor('#287d9a'));p.setPen(QPen(QColor('white'),1))
  for x,y in pts:
   px=left+10+(x-xmin)/dx*(right-left-20);py=bottom-10-(y-ymin)/dy*(bottom-top-20) if key=='PCA' else (top+bottom)/2;p.drawEllipse(QPointF(px,py),4.5,4.5)
  p.end()
