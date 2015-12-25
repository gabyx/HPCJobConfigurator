# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import shutil
import os.path as path

from lxml import etree  as ET
from lxml import objectify

from HPCJobConfigurator.jobGenerators.dictionaryAdjuster import DictionaryAdjuster

class AdjusterContinue(DictionaryAdjuster) : 
    
    def __init__(self,jobGenModules):
        
        super(AdjusterContinue,self).__init__(jobGenModules) 
    
    def __call__(self, generator, inputFile, outputFile, configDict, lastConfigDicts, **kwargs):
        
        """ Adjusts the scene file xml then writes the scene file to configDict["RigidBodySim"]["sceneFile"] 
            and then interpolates all remaining options still in the xml with the replacementDict which contains
            the same options as the configDict , the configDict type is just nicer to access, e.g {"sec1" : {"opt1" : 1} , "sec2" : {"opt1" : 1}} 
        """
        replacementDict = self.cf.flattenDict(configDict);
        
        if not configDict.Cluster.submitArgsChainJob :
            raise ValueError("You try to succesively continue the rigidbody simulation but ${Cluster:submitArgsChainJob} is empty! Is that correct?")
        
        jobIdx = int(configDict.Job.jobIdx)
        
        if jobIdx == 0:
            print( "AdjusterContinue:: No scene file adjusting for first job! ")
            self.writeTemplate(inputFile, replacementDict, outputFile)
            return 
            
        print( "AdjusterContinue:: Adjust scene file %s  ---->  %s" % (inputFile,outputFile))
        
        lastConfigDict = lastConfigDicts[-1]
        
        # Change SCENE FILE ===================================================================================    
        # load scene file and adjust global intial condition
        f = open(inputFile, 'r') 
        tree = ET.parse(f)
        root = tree.getroot()
        ####    
        for elem in root.getiterator():
            if not hasattr(elem.tag, 'find'): continue  # (1)
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i+1:]
        objectify.deannotate(root, cleanup_namespaces=True)
        ####
        
        # find scenesettings
        s = root.find("SceneSettings")
        if s is None:
            raise ValueError("Your scene file: %s has not a single SceneSettings node!" % configDict.RigidBodySim.sceneFileTemplate)
        
        # finde globale initial condition    
        g = s.find("GlobalInitialCondition")
        if(lastConfigDict.RigidBodySim.simFilePath == configDict.RigidBodySim.simFilePath):
            raise NameError(
            """Something wrong with simFilePath, this 
            jobIdx %i has same file path %s which is the same as the previous jobs path : %s""" 
            % (jobIdx,configDict.RigidBodySim.simFilePath,lastConfigDict.RigidBodySim.simFilePath) )
        
        ginit = {"file":"","whichState":"end" , "readVelocities":"true", "useTimeToContinue":"true"}
        ginit["file"] = lastConfigDict.RigidBodySim.simFilePath


        if g is None:
            s.append(ET.Element("GlobalInitialCondition", ginit))
        else:
            g.attrib.update(ginit)
        
        # =======================================================================================================
       
        # replace all options still in the xml
        s = ET.tostring(root,encoding="unicode", method='xml')
        self.writeTemplateStr( s, replacementDict,  outputFile )       
    
    def get_namespace(element):
      m = re.match('\{.*\}', element.tag)
      return m.group(0) if m else ''
