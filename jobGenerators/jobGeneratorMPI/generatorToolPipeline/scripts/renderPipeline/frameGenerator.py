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
        
        self.cf = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
        self.gSFI = jobGenModules["getSimFileInfos"]

        
        self.pipelineSpecs = pipelineSpecs
        self.pipelineTools = pipelineSpecs["pipelineTools"]
        
    def __call__(self,simFiles, startIdx,endIdx,increment,skipFirstState,simInfoApp, checkForDoubleTimes = True):
        
        print("FrameGenerator Render Pipeline ==========================")

        if increment <= 0:
             raise ValueError("increment <= 0")
        if startIdx < 0 :
            raise ValueError("startIdx < 0")
        if endIdx != -1  and (endIdx < startIdx) :
            raise ValueError("endIdx < startIdx, needs to be either -1 or greater or equal than startIdx")    
        
        # get number of states from the files
        # build a list of frame indices, in sequence with the sim files arguments
        # key = simfile ,  value = dict( key=idx, dict(stateIdx, time , frameNr) )
        framesPerFile = {};

        infos = self.gSFI.getSimFileInfos(simFiles, sIdx = startIdx, eIdx= endIdx, incr = increment, 
                                skipFirstState = skipFirstState,
                                app=simInfoApp);

        for f,info in infos.items():
            startIdx = info.resampleInfo.startIdx;
            endIdx = info.resampleInfo.endIdx;
            incr = info.resampleInfo.increment;
            stateIndices = info.resampleInfo.stateIndices
            
            if stateIndices is None:
                # this is a file where we dont take any states
                continue
            
            times = [ info.timeList[i] for i in stateIndices ]
            
            p = os.path.abspath(f) 
            
            def updateDict(d,dd):
                for key in dd["copyToFrame"]:
                    if key in d :
                        raise ValueError("Key %s exists already in dict: %s" %(key,str(d)))
                    d[key] = copy.deepcopy(dd[key])
                return d
                
            framesPerFile[p] =  [ { 
                                    "tools": {
                                        "converter" : 
                                           updateDict({
                                            "stateIdx":t[0], 
                                            "time":t[1], 
                                            "simFile": p , 
                                            "uuid" : str(self.cf.makeUUID(p)), 
                                            "status":"convert"
                                           }, self.pipelineTools["converter"] ) , 
                                        "renderer": 
                                            updateDict({
                                            "frameIdx":0, 
                                            "status":"render"
                                            },self.pipelineTools["renderer"] )
                                    },
                                "fileMover" : list([])
                               }
                               for t in zip(idx,times)  ]    
            
        # assign a frame number to each stateIdx in framesPerFile, order according to time
        allFrames = []
        framesPerIdx = {}
        for path,states in framesPerFile.items():
            allFrames.extend(states)
        allFrames = sorted(allFrames, key=lambda x: x["tools"]["converter"]["time"])
        for i,v in enumerate(allFrames):
            v["tools"]["renderer"]["frameIdx"]=i  
            framesPerIdx[i] = v;
        
        
        t = [ (f["tools"]["converter"]["time"], f["tools"]["renderer"]["frameIdx"]) for f in allFrames]
        print("Frames from simfiles:", t )  
        
              
        # Check for double times entries (this is not good)
        if(checkForDoubleTimes):
          for i in range(0,len(t)-1):
              if t[i][0] == t[i+1]:
                  raise ValueError("WARNING: Duplicate time: %i , seen at frame: %i and %i " % (t[i][0],t[i][1],t[i+1][1]))
        
        
    
        print("Job frames to render: ===================================" )
        for file,frames in framesPerFile.items():
            frames.sort(key=lambda f: f["tools"]["converter"]["stateIdx"])
            print( "Job state list for file %s :\n " % file + str([ (f["tools"]["renderer"]["frameIdx"] ,f["tools"]["converter"]["time"]) for f in framesPerFile[file] ] ) )
        
        print("=========================================================" )

        return (allFrames,framesPerIdx,framesPerIdx.values())
        # return all frames and frames per frameIdx, and a sortedFrames list which is used to distribute over the processes 