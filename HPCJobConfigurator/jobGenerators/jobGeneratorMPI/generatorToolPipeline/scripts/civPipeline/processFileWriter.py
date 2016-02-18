# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os

import xml.etree.ElementTree as ET


class CorrelatorProcessFileWriter:
    def __init__(self,pipelineSpecs,jobGenModules):
      
      self.cF = jobGenModules["commonFunctions"]
      self.iH = jobGenModules["importHelpers"]
      
      self.pipelineSpecs = pipelineSpecs
    
    def write(self,processFrames,processFile, processClass , **kargs):
        for procIdx, fList in enumerate(processFrames):
            
            frames = []
            
            # add all additional keyword arguments to general settings
            processSettings = kargs
            
            c = { "frames" : frames, "processSettings" : processSettings, "processClass" : processClass }
            
            for frame in fList :
                correlator = frame["tools"]["correlator"]
                if correlator["status"] != "finished": 
                    
                    f = {'inputFiles' : correlator["inputFiles"], 
                          'frameIdx': correlator["frameIdx"] } 
                    frames.append(f)
                
            # sort frames
            frames.sort(key=lambda fr: fr["frameIdx"])
                                  
            f = open(processFile.format(procIdx),"w+")
            self.cF.jsonDump(c,f,indent=4)
            f.close()
        
        print("Wrote correlator process files for all process indices")   
       

class ConverterProcessFileWriter:
    
    def __init__(self,pipelineSpecs,jobGenModules):
      
      self.cF = jobGenModules["commonFunctions"]
      self.iH = jobGenModules["importHelpers"]
      
      self.pipelineSpecs = pipelineSpecs
    
    def write(self,processFrames, processFile, processClass, **kargs):
         
        for procIdx, fList in enumerate(processFrames):
            
            frames = []
            # add all additional keyword arguments to general settings
            processSettings = kargs
        
            c = { "frames" : frames, "processSettings" : processSettings , "processClass" : processClass }
            
            for frame in fList :
                converter = frame["tools"]["converter"]
                if converter["status"] != "finished": 
                    f = { 'inputFiles' : converter["inputFiles"],
                          'inputFileIndices' : converter["inputFileIndices"],
                          'outputFiles' :  converter["outputFiles"],
                          'frameIdx': frame["tools"]["correlator"]["frameIdx"] }
                
                    
                    frames.append(f)
                
            # sort frames
            frames.sort(key=lambda fr: fr["frameIdx"])
                                  
            f = open(processFile.format(procIdx),"w+")
            self.cF.jsonDump(c,f,indent=4)
            f.close()
        print("Wrote converter process files for all ranks")