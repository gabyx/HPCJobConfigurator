# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

#!/usr/bin/env python3 

import sys,os, subprocess,shutil,io
import xml.etree.ElementTree as ET
from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF

converterEnvDefault = "SIMCONV"


class SimFileInfo(object):
    def __str__(self):
        return "SimInfo: " + str(vars(self))
class ResampleInfo(object):
    def __str__(self):
        return "ResampleInfo: " + str(vars(self))



def getSimFileInfos(simFiles, app="Converter", converterEnv = converterEnvDefault, sIdx=0, eIdx=-1, incr = 1, skipFirstState = True , returnList= False):
    
    simConverter = shutil.which(app)
    
    if not simConverter:
        try:
            simConverter = os.environ[converterEnv]
        except:
            raise RuntimeError( "Error: can't read environment variable %s, maybe not defined, nor could the app %s be found!" % (converterEnv, app) )
    
    
    if isinstance(simFiles,str):
        simFiles = simFiles.split(" ")
    
    standardOut = subprocess.check_output([simConverter,"siminfo","-i"]
                                          +simFiles 
                                          + ['--startIdx', str(sIdx), '--endIdx',str(eIdx), '--increment', str(incr)] 
                                          + (["--skipFirstState"] if skipFirstState else []) ,stderr=subprocess.DEVNULL )
    #print("output: ", standardOut)
    xmlDoc = ET.fromstring(standardOut); 
    
    if returnList:
      l = []
    else:
      l = {}
      
    for simNode  in xmlDoc.findall("SimFile"):
        
        s = SimFileInfo()
        
        s.path = simNode.attrib['path'];
        s.nBytes = int(simNode.attrib['nBytes']);
        s.nSimBodies = int(simNode.attrib['nSimBodies']);
        s.nDOFqBody = int(simNode.attrib['nDOFqBody']);
        s.nDOFuBody = int(simNode.attrib['nDOFuBody']);
        s.nStates = int(simNode.attrib['nStates']);
        s.nBytesPerState = int(simNode.attrib['nBytesPerState']);
        s.nBytesPerBody = int(simNode.attrib['nBytesPerBody']);
        s.nBytesPerQBody = int(simNode.attrib['nBytesPerQBody']);
        s.nBytesPerUBody = int(simNode.attrib['nBytesPerUBody']);
        s.addBytesBodyType = int(simNode.attrib['addBytesBodyType']);
        s.addBytesBodyType = int(simNode.attrib['addBytesBodyType']);
        s.nAdditionalBytesPerBody = int(simNode.attrib['nAdditionalBytesPerBody']);
        s.readVelocities = bool(simNode.attrib['readVelocities']);
        s.timeList = [float(t) for t in simNode.attrib['timeList'].split(" ") ];
        
        
        resampleNode = simNode.find("Resample");
        s.resampleInfo = ResampleInfo();
        s.resampleInfo.startIdx = int(resampleNode.attrib["startIdx"]);
        s.resampleInfo.endIdx =int(resampleNode.attrib["endIdx"]);
        s.resampleInfo.increment = int(resampleNode.attrib["increment"]);
        
        
        # load stateIndices if possible
        indNode = resampleNode.find("Indices")
        if indNode is not None:
          s.resampleInfo.stateIndices = [ int(s) for s in indNode.text.strip().split(" ")]
        else:
          s.resampleInfo.stateIndices = None
        
        if returnList:
          l.append(s)
        else:
          l[s.path] = s
      
    return l;
    