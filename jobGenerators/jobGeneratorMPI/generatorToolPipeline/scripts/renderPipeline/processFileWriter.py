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

class RenderProcessFileWriter:
    
    def __init__(self,pipelineSpecs, jobGenModules):
      
        self.cf = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
        
        self.pipelineSpecs = pipelineSpecs
    
    def write(self,processFrames, processFile):
        for procIdx, fList in enumerate(processFrames):
            
            c = []
            for frame in fList:
                renderer = frame["tools"]["renderer"]
                if renderer["status"] != "finished" :
                    c.append ( {'inputFile' : renderer["inputFiles"][0], 
                                'frameIdx': renderer["frameIdx"] 
                               } )
                                   
            
            c.sort(key=lambda fr: fr["frameIdx"])                      
            f = open(processFile.format(procIdx),"w+")
            self.cf.jsonDump(c,f,indent=4)
            f.close()
        
        print("Wrote render process files for all process indices")   
       

class ConverterProcessFileWriter:
    
    def __init__(self,pipelineSpecs, jobGenModules):
      
        self.cf = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
        
       self.pipelineSpecs = pipelineSpecs
    
    def write(self,processFrames, processFile):
         
        for procIdx, fList in enumerate(processFrames):
            
            # sort fList according to simFile and then according to stateIdx
            fList.sort(key=lambda f: (f["tools"]["converter"]["simFile"], f["tools"]["converter"]["stateIdx"] ) )
            
            root = ET.Element("Converter")
            lastFile = None
            for frame in fList:
                    converter = frame["tools"]["converter"]
                    f = converter["simFile"]
                    if  f != lastFile:
                        lastFile = f
                        fNode = ET.Element("File");
                        root.append(fNode)
                        fNode.attrib['simFile'] = f
                        fNode.attrib['uuid'] = str(self.cf.makeUUID(f));

                    if converter["status"] =="finished":
                        continue
                        
                    s = ET.Element("State");
        
                    s.attrib['stateIdx']   = str(converter["stateIdx"])
                    s.attrib['time']       = str(converter["time"])
                    s.attrib['outputFile'] = converter["outputFiles"][0]["file"]
                    s.attrib['mappedIdx']   = str(frame["tools"]["renderer"]["frameIdx"])
                    fNode.append(s)
            tree = ET.ElementTree(root);

            f = open(processFile.format(procIdx),"w+")
            f.write(cf.prettifyXML(root))
            f.close()
        print("Wrote converter process files for all ranks")