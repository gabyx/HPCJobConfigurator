# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os,copy

class FrameGenerator:
    
    def __init__(self,pipelineSpecs, jobGenModules):
      
        self.cF = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
        self.gSFI = jobGenModules["getSimFileInfos"]
        
        self.pipelineSpecs = pipelineSpecs
        self.pipelineTools = pipelineSpecs["pipelineTools"]
        
    def __call__(self, startIdx,endIdx,increment):
        
        print("FrameGenerator CIV Pipeline =============================")

        
        if increment <= 0:
             raise ValueError("increment <= 0")
        if startIdx < 0 :
            raise ValueError("startIdx < 0")
        if endIdx != -1  and (endIdx < startIdx) :
            raise ValueError("endIdx < startIdx, needs to be either -1 or greater or equal than startIdx")    
        
        framesPerIdx = {};
        
        def updateDict(d,dd):
            for key in dd["copyToFrame"]:
                if key in d :
                    raise ValueError("Key %s exists already in dict: %s" %(key,str(d)))
                d[key] = copy.deepcopy(dd[key])
            return d
        
        allFrames =  [ { "tools" : { 
                                 "converter" : 
                                   updateDict({
                                    "status": "not-finished",
                                   }, self.pipelineTools["converter"] ) , 
                                "correlator": 
                                    updateDict({
                                    "frameIdx":t, 
                                    "status":"not-finished",
                                    },self.pipelineTools["correlator"] ), 
                                
                               }, "fileMover" : list([]) }
                               for t in range(startIdx,endIdx,increment)  ]
        
        
        framesPerIdx = dict( ( (f["tools"]["correlator"]["frameIdx"],f) for f in allFrames) )
        
     
    
        print("Job frames for correlation: =============================" )
        print( [k for k in framesPerIdx.keys()] )
        print("=========================================================" )
                 
        return (allFrames,framesPerIdx,framesPerIdx.values())
        # return all frames and frames per frameIdx, and a sortedFrames list which is used to distribute over the processes 