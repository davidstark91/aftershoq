'''
Created on 18 Jun 2018

@author: martin
'''

from .interface import Interface
import datetime
import xml.etree.ElementTree as ET
from lxml import etree
import utils.systemutil as su

class Inextnano(Interface):
    '''
    classdocs
    '''
    
    nn_numpar = {"acc_Emax" : 2.5,
                 "screening_model": 1, # 1, 2, 3 for av. e-temp
                 "gain_method" : 0, # -1, 0, 1, 2
                 "gain_maxits" : 50,
                 "gain_tol" : 0.001,
                 "gain_vmin" : 0,
                 "gain_vmax" : 0.5,
                 "T_offset": 140,
                 "etemp_acc": 0.05,
                 "etemp_screen": 200,
                 "use-phenom-temp":False,
                 "use-selfcons-temp":False,
                 "E-plots" : True,
                 "E-gain" : True,
                 "E-plots-spacing" : 0.0005,
                 "E-gain-omega" : 0.010,
                 "imp-strength" : 1.0,
                 "LO-strength" : 1.0,
                 "e-e-strength": 1.0,
                 "Npint" : 5,
                 "Emin_shift" : 0.,
                 "Emax_shift" : 0.,
                 "tol_GF" : 0.0005,
                 "tol_curr" : 0.0005,
                 "tol_GF_min" : 0.010,
                 "Nthreads" : 0}


    def __init__(self, binpath, pltfm, wellmaterial):
        '''
        Constructor
        '''
        
        super(Inextnano,self).__init__(binpath, pltfm)
        self.numpar.update(self.nn_numpar)
        self.prog = binpath + "nextnano.QCL.exe"
        self.wellmat = wellmaterial
        self.latmat = wellmaterial
        self.processes= []
        self.datpath = "/IV/"
        self.separators = [2.0, 22.0]
        self.input = "AGS.xml"
        self.license = "license.txt"
        self.dbfile = "Material_Database.xml"
        
    def __str__(self):
        return "Inextnano.QCL"
    
    
    def runStructures(self,structures,path,runprog=True):
        '''Run simulations for all structures in the given structure list with
        the base path "path". This method dispatches all processes and returns
        the user has to wait for processes to finish before accessing results.
        
        Stores started processes in self.processes
        '''
        for s in structures:
            self.writeInputFile(s, path)
            spath = path + "/" + s.dirname
            
            '''nextnano.QCL.exe <input file name> <output folder name> 
                          <material database name> <License file name>'''
            
            input = spath + "/" + self.input
            output = spath + "/" + self.datpath
            dbfile = path + "/" + self.dbfile
            license = path + "/" + self.license
            
            prog = "cmd"
            nn_args = ["/c", self.binpath, input, output, dbfile, license]
            proc = self.pltfm.submitjob(prog, nn_args, spath + self.datpath)
            self.processes.append(proc)
        
        return self.processes
    
    def gatherResults(self,structures,path,pathresults=None, runprog=None):
        '''Write results to pathresults/results.log and run hdiag and bandplot
        in pathwd/s.dirname/self.datpath/eins/x/ for each i and x. Stores WS 
        resutls as a new attribute levels[directory][WS level][data field] in 
        each Structure object in the list structures.
        
        TODO: Overwrite parent implementation
        '''
        pass
        
    def writeInputFile(self, structure, path):
        
        unm = {"unit":"nm"}
        uT = {"unit":"K"}
        umeV = {"unit": "meV"}
        
        spath = path + "/" + structure.dirname
        su.mkdir(spath)
        
        root = etree.Element("nextnano.QCL", attrib={"Version": "1.1.5"})
        
        # Headers:
        
        author = "[aftershoq] " + str(datetime.datetime.now()) + ""
        content = "This is an autogenerated input file."
        header = etree.SubElement(root, "Header")
        etree.SubElement(header, "Author").text = author
        etree.SubElement(header, "Content").text = content
        
        # Sweep parameters:
        # TODO: implement Temperature sweep
        
        if(self.numpar["Nefield"] > 1):
            
            swpar = etree.SubElement(root, "SweepParamters")
            etree.SubElement(swpar, "SweepType").text = "Voltage"
            etree.SubElement(swpar, "Min").text = str(self.numpar["efield0"]*1000)
            efdmax = (self.numpar["defield"]*(self.numpar["Nefield"]-1) + 
                      self.numpar["efield0"])
            etree.SubElement(swpar, "Max").text = str(efdmax*1000)
            etree.SubElement(swpar, "Delta").text = str(self.numpar["defield"]*1000)
        
        else:
            bias = etree.SubElement(root, "Bias")
            etree.SubElement(bias, "PotentialDrop", umeV).text \
                             = str(self.numpar["efield0"]*1000)
            
        
        # Temperature:
        etree.SubElement(root, "Temperature", uT).text \
            = str(self.numpar["Tlattice"])
            
        # Materials:
        
        materials = etree.SubElement(root, "Materials")
        
        matstr = []
        for l in structure.layers:
            if str(l.material) in matstr:
                continue
            
            matstr.append(str(l.material))
        
            mat = etree.SubElement(materials, "Material")
            etree.SubElement(mat, "Name").text = str(l.material)
            etree.SubElement(mat, "Alias").text = str(l.material)
            etree.SubElement(mat, "Effective_mass_from_kp_parameters").text\
                = "yes"
            if(l.material.x is not None):
                etree.SubElement(mat, "Alloy_Composition").text\
                = str(l.material.x)
        
        etree.SubElement(materials, "NonParabolicity").text = "yes"
        etree.SubElement(materials, "UseConductionBandOffset").text = "yes"
        
        # Structure:
        
        SL = etree.SubElement(root, "Superlattice")
        for l in structure.layers:
            layer = etree.SubElement(SL, "Layer")
            etree.SubElement(layer, "Material").text = str(l.material)
            etree.SubElement(layer, "Thickness", unm).text = str(l.width)
                             
        # Doping:
        for d in structure.dopings:
            doping = etree.SubElement(SL, "Doping")
            etree.SubElement(doping, "DopingStart", unm).text \
                = str(d[0])
            etree.SubElement(doping, "DopingEnd", unm).text \
                = str(d[1])
            etree.SubElement(doping, "Doping_Specification").text \
                = "1"
            etree.SubElement(doping, "Doping_Density").text \
                = str(d[2])
        
        # Scattering:
        
        scatt = etree.SubElement(root, "Scattering")
        etree.SubElement(scatt, "Material_for_scattering_parameters").text\
            = str(self.wellmat)
            
        # IFR: 
        
        IFR = etree.SubElement(scatt, "Interface_Roughness")
        if(self.numpar["use-ifr"]) == False:
            etree.SubElement(IFR, "Amplirude_in_Z", unm).text\
            = "0"
        else:
            etree.SubElement(IFR, "Amplirude_in_Z", unm).text\
                = str(structure.layers[0].eta)
        # TODO: Choose autocorrelation function!
        etree.SubElement(IFR, "InterfaceAutoCorrelationType", unm).text = "0"
        etree.SubElement(IFR, "Correlation_Length_in_XY", unm).text\
             = str(structure.layers[0].lam)
        
        # Imp:
        
        etree.SubElement(scatt, "Model_Temperature_for_Screening").text\
            = str(self.numpar["screening_model"])

        if (self.numpar["screening_model"] == 1):
            etree.SubElement(scatt, "Temperature_Offset_parameter").text\
                =str(self.numpar["T_offset"])
        elif (self.numpar["screening_model"] == 2):
            etree.SubElement(scatt, 
                "Accuracy_Self_consistent_Electron_Temperature").text\
                =str(self.numpar["etemp_acc"])
        elif (self.numpar["screening_model"] == 3):
            etree.SubElement(scatt, "Electron_Temperature_for_Screening").text\
                =str(self.numpar["etemp_screen"])
        
        etree.SubElement(scatt, "Phenomenological_Electron_Temperature").text\
            =("yes" if self.numpar["use-phenom-temp"] else "no")
        
        etree.SubElement(scatt, "Self_consistent_Electron_Temperature").text\
            =("yes" if self.numpar["use-selfcons-temp"] else "no")
        
        # TODO: add tight binding option (<Analysis>)
        # TODO: add Crystal structure (<Crystal>)
        
        etree.SubElement(scatt, "ImpurityScattering_Strength").text\
            = str(self.numpar["imp-strength"])
            
        # Alloy:
        
        etree.SubElement(scatt, "Alloy_scattering").text\
            = ("yes" if self.numpar["use-alloy"] else "no")
            
        # Accoustic phonons:
        
        etree.SubElement(scatt, "Acoustic_Phonon_Scattering").text\
            = ("yes" if self.numpar["use-acc"] else "no")
        
        etree.SubElement(scatt, "AcousticPhonon_Scattering_EnergyMax",
                         umeV).text = str(self.numpar["acc_Emax"])
                         
        # Optical phonons:
        if(self.numpar["LO-strength"] != 1.0):
            
            etree.SubElement(scatt, "Tune_LO_Phonon_Scattering>").text = "yes"
            etree.SubElement(scatt, "LO_Phonon_Coupling_Strength").text\
                = str(self.numpar["LO-strength"])
        
        # e-e:
        etree.SubElement(scatt, "Electron_Electron_Scattering").text\
            = ("yes" if self.numpar["use-e-e"] else "no")
            
        if(self.numpar["use-e-e"] and self.numpar["e-e-strength"]!=1.0):
            etree.SubElement(scatt, "Tune_Elect_Elect_Scattering_Strength").text="yes"
            etree.SubElement(scatt, "Elect_Elect_Scattering_Strength").text\
                =str(self.numpar["e-e-strength"])
                
        
        # Poisson:
        etree.SubElement(root, "Poisson").text\
            = ("yes" if self.numpar["use-poisson"] else "no")
            
        # Lateral motion:
        # Default is same as wellmat, but can be set in Inextnano.latmat
        etree.SubElement(root, "Material_for_lateral_motion").text\
            = str(self.latmat)
        lateral = etree.SubElement(root, "Lateral_motion")
        Deltak = self.numpar["Ekmax"]/float(self.numpar["Nk"])
        etree.SubElement(lateral, "Value").text = str(Deltak*1000.)
        
        # Simulation parameters:
        
        simpar = etree.SubElement(root, "Simulation_Pramater")
        etree.SubElement(simpar, "Coherence_length_in_Periods").text\
            = str(self.numpar["Nper"])
        etree.SubElement(simpar, "Spatial_grid_spacing", unm).text\
            = str(structure.length/float(self.numpar["Nz"]))
        etree.SubElement(simpar, 
                         "Number_of_lateral_periods_for_band_structure").text\
                         = str(self.numpar["Npint"])
        DeltaE = self.numpar["Emax"]/float(self.numpar["NE"])
        etree.SubElement(simpar, "Energy_grid_spacing", umeV).text\
            = str(DeltaE*1000.)
        etree.SubElement(simpar, "Emin_shift", umeV).text\
            = str(self.numpar["Emin_shift"]*1000.)
        etree.SubElement(simpar, "Emax_shift", umeV).text\
            = str(self.numpar["Emax_shift"]*1000.)
            
        etree.SubElement(simpar, "Energy_Range_Lateral", umeV).text\
            = str(self.numpar["Ekmax"]*1000.)
        etree.SubElement(simpar, "Energy_Range_Axial", umeV).text\
            = str(self.numpar["Emax"]*1000.)
            
        etree.SubElement(simpar, "Convergence_Value_GF").text\
            = str(self.numpar["tol_GF"])
        etree.SubElement(simpar, "Convergence_Value_Current").text\
            = str(self.numpar["tol_curr"])
            
        etree.SubElement(simpar, "N_max_iterations").text\
            = str(self.numpar["maxits"])
        
        etree.SubElement(simpar, "Convergence_Minimum").text\
            = str(self.numpar["tol_GF_min"])
            
        etree.SubElement(simpar, "Maximum_Number_of_Threads").text\
            = str(self.numpar["Nthreads"])
            
        # Output:
        output = etree.SubElement(root, "Output")
        etree.SubElement(simpar, "EnergyResolvedPlots").text\
            = ("yes" if self.numpar["E-plots"] else "no")
        etree.SubElement(simpar, "EnergyResolvedPlots_MinimumEnergyGridSpacing",
                        umeV).text = str(self.numpar["E-plots-spacing"]*1000.)
        
        etree.SubElement(simpar, "EnergyResolved_Gain").text\
            = ("yes" if self.numpar["E-gain"] else "no")
        etree.SubElement(simpar, "EnergyResolved_Gain_PhotonEnergy", umeV).text\
            = str(self.numpar["E-gain-omega"]*1000.)
        
        # Gain:
        gain = etree.SubElement(root, "Gain")
        etree.SubElement(gain, "GainMethod").text\
            = str(self.numpar["gain_method"])
            
        if(self.numpar["gain_method"] == 0 or self.numpar["gain_method"] == 3):
            etree.SubElement(gain, "dE_Phot", umeV).text\
                = str(self.numpar["domega"]*1000.)
            etree.SubElement(gain, "Ephoton_Min", umeV).text\
                = str(self.numpar["omega0"]*1000.)
            om_max = self.numpar["omega0"] + \
                self.numpar["domega"]*(self.numpar["Nomega"]-1)
            etree.SubElement(gain, "Ephoton_Max", umeV).text\
                = str(om_max*1000.)
        if(self.numpar["gain_method"] == 1 or self.numpar["gain_method"] == 3):
            etree.SubElement(gain, "dE_Phot_Self_Consistent", umeV).text\
                = str(self.numpar["domega"]*1000.)
            etree.SubElement(gain, "Ephoton_Min_Self_Consistent", umeV).text\
                = str(self.numpar["omega0"]*1000.)
            om_max = self.numpar["omega0"] + \
                self.numpar["domega"]*(self.numpar["Nomega"]-1)
            etree.SubElement(gain, "Ephoton_Max_Self_Consistent", umeV).text\
                = str(om_max*1000.)
            
            etree.SubElement(gain, "MaxNumber_SelfConsistent_Iterations").text\
                = str(self.numpar["gain_maxits"])
            etree.SubElement(gain, "ConvergenceFactor_Gain_SelfConsistent").text\
                = str(self.numpar["gain_tol"])
                
        if(self.numpar["gain_method"] > -1):
            etree.SubElement(gain, "Vmin").text\
                = str(self.numpar["gain_vmin"]*1000.)
            etree.SubElement(gain, "Vmax").text\
                = str(self.numpar["gain_vmax"]*1000.)
        
    
        self.tree = etree.ElementTree(root)
        
        file = spath + "/" + self.input
        self.tree.write(file, xml_declaration=True, encoding="utf-8", pretty_print=True)
        
    def writeMaterialDB(self):
        '''
        <Overwrite_Material_Database>
        <Material>
          <Name>GaAs</Name>
          <ConductionBandOffset Unit="eV">2.979</ConductionBandOffset>
          <BandGap Unit="eV">1.519</BandGap>
          <EpsStatic>12.93</EpsStatic>
        </Material>
        </Overwrite_Material_Database>     
        '''
        pass
    
    def getMerit(self,structure,path):
        '''Returns the merit function evaluated for the Structure structure,
        with base path "path". 
        
        TODO: Overwrite parent implementation
        '''
        return "ERROR"
        