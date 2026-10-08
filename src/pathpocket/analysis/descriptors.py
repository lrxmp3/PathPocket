import sys
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors,Crippen,rdMolDescriptors,Lipinski,QED,FilterCatalog
from rdkit.Chem.Scaffolds import MurckoScaffold

def describe(m):
    try:from rdkit.Contrib.SA_Score import sascorer
    except ImportError:
        sys.path.insert(0,str(Path(sys.prefix)/'share/RDKit/Contrib/SA_Score'));import sascorer
    mol=Chem.RemoveHs(m)
    row=dict(MW=Descriptors.MolWt(mol),cLogP=Crippen.MolLogP(mol),TPSA=rdMolDescriptors.CalcTPSA(mol),HBD=Lipinski.NumHDonors(mol),HBA=Lipinski.NumHAcceptors(mol),rotatable_bonds=Lipinski.NumRotatableBonds(mol),ring_count=rdMolDescriptors.CalcNumRings(mol),aromatic_ring_count=rdMolDescriptors.CalcNumAromaticRings(mol),fractionCSP3=rdMolDescriptors.CalcFractionCSP3(mol),formal_charge=Chem.GetFormalCharge(mol),SA=float(sascorer.calculateScore(mol)),QED=QED.qed(mol),scaffold=MurckoScaffold.MurckoScaffoldSmiles(mol=mol) or 'ACYCLIC')
    for name,enum in [('PAINS',FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS),('Brenk',FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)]:
        params=FilterCatalog.FilterCatalogParams();params.AddCatalog(enum);row[name]=FilterCatalog.FilterCatalog(params).HasMatch(mol)
    return row
