# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os

class RenderInfoFileWriter:
    
    def __init__(self,pipelineSpecs, jobGenModules):
        
        self.cf = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
        self.gSFI = jobGenModules["getSimFileInfos"]
        
        self.pipelineSpecs = pipelineSpecs
    
    def write(self,processFrames,infoFile):
        
        simFiles = self.pipelineSpecs["frameGenerator"]["arguments"]["simFiles"]
        
        if isinstance(simFiles,str):
            simFiles = simFiles.split(" ")
        
        hashes=[]
        for f in simFiles:
            hashes.append( {'absPath': f, 'uuid': self.cf.makeUUID(f) } ) 
        
        frameInfo = []
        for procIdx, fList in enumerate(processFrames):
            for frame in fList:
                frameInfo.append( {"converter":frame["tools"]["converter"], "renderer": frame["tools"]["renderer"]} )

        
        f = open(infoFile,"w+")
        self.cf.jsonDump({"hashes" : hashes , "frameInfo" : frameInfo},f,indent=4)
        f.close()
        print("Wrote sim render info to: %s" % infoFile)

       
