# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 10:47:37 2019

@author: David
"""

from aftershoq.qcls import Deutsch2017
from aftershoq.qcls import EV1125
from aftershoq.interface import Inextnano
from aftershoq.materials import InGaAs
from aftershoq.numerics.runplatf import Local

#%%

nnroot = "D:\\nextnano\\nextnano.QCL\\2019_06_05\\nextnano.QCL"
lic = "D:\\nextnano\\LicenseLicense_nnQCL.lic"
folder_input = "C:\\Users\\David\\OneDrive\\Nextnano\\Heterostructures_Simulations\\InGaAs_AlInAs_THz_QCLs"
model = Inextnano(nnroot, Local(), InGaAs(), lic)


#s = Deutsch2017()
s = EV1125()
for l in s.layers:
    print(l.material.name)

import numpy as np  
np.round(s.layers[0].material.params['Ec'] - s.layers[1].material.params['Ec'],3)

#%%

for l in s.layers:
    if l.material.name == "In_0.53GaAs":
        l.material.name = "In(x)Ga(1-x)As"
        
for l in s.layers:
    if l.material.name == "Al_0.48InAs":
        l.material.name = "Al(x)In(1-x)As"

model.numpar["efield0"] = 0.050
model.numpar["defield"] = 0.005
model.numpar["Nefield"] = 5
model.numpar["NE"] = 400
model.numpar["Nk"] = 400
model.numpar["Nz"] = 100

model.writeInputFile(s,folder_input)
