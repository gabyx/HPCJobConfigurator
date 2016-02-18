# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

#!/usr/bin/env python3 

# Prepares the render folder for cluster rendering



import sys,os, subprocess, ctypes,traceback


if sys.version_info[0] != 3:
    print("This script is only python3 compatible!")
    exit(1)

import jsonpickle
import itertools
from argparse import ArgumentParser
from attrdict import AttrMap

from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF
from HPCJobConfigurator.jobGenerators.stringExpression import Expression as StrExpr

from . import getSimFileInfos 

class MyOptParser(ArgumentParser):
    def error(self,msg):
        self.print_help()
        raise ValueError("Error occured: " + msg)



STATUS_FINISHED = "finished"
STATUS_RECOVER = "recover"
        

def walkDependencies(stack,files):
    
     
    invalidFrame = False
     
    while stack:               
        currFile = stack[-1]            
        # only check dependencies of this file if it has not already been done
        if "depCheck" not in currFile or not currFile["depCheck"]:
            
                # build dep files
                if currFile["status"] == STATUS_FINISHED :
                    # for finished files we dont need to check dependencies, but do it anyway 
                    # if we have some depId which is not found it does not matter! (file is finished anyway)
                    depFiles = [ files["id"][depId] for depId in currFile["dependencies"] if depId in files["id"] ]
                elif currFile["status"] == STATUS_RECOVER: 
                    try:
                        depFiles = [ files["id"][depId] for depId in currFile["dependencies"] ]
                    except KeyError as e:
                        raise ValueError("For recoverable file %s could not locate dependency id : " % currFile["absPath"] + str(e) )
                else:
                   raise ValueError("Status %s for file %s not valid!" % (currFile["status"], currFile["absPath"]))
                
                try:
                    # For all dependecy files check status
                    for depFile in depFiles:
                       if depFile["status"] == STATUS_RECOVER:
                           print("""File %s depends on file %s which also 
                                    has status recover. It should be finished instead! -> classify frame as invalid """ 
                                    % (currFile["absPath"],depFile["absPath"]) )
                           raise
                           
                    currFile["depCheck"] = True
                    
                    # push all dep files on the stack
                    stack += depFiles
                   
                except:
                   print("Could not resolve dependency for file: %s" % currFile)
                   invalidFrame = True
                   stack = None
           
        else:
            #already checked
            stack.pop()
        #endif
    # endwhile
    return invalidFrame

def writeFileMoverProcessFile(pipelineSpecs,processFrames):
    
    pipelineTools = pipelineSpecs["pipelineTools"]
    toolTasks = []
    
    # Set up all input/output folders for each tool
    for toolName,tool in pipelineTools.items():
        toolTasks.append( {"type":"makeDirs", "dir" : tool["outputDir"]} )
        toolTasks.append( {"type":"makeDirs", "dir" : tool["inputDir"]} )
    
    # Set up simlinks (make link to outputs in input folders of parent tools)
    if "linkAllTools" in pipelineSpecs["fileMover"] and pipelineSpecs["fileMover"]["linkAllTools"]:
        for toolName,tool in pipelineTools.items():
            for parentName in tool["parents"]:
                d = pipelineTools[parentName]["inputDir"]
                toolTasks.append( {"type":"symlink", "to" : os.path.join(d, toolName), "from" :  tool["outputDir"]} )
    
    # Set up all other dirs in makeDirectories
    if "additionalTasks" in pipelineSpecs["fileMover"]:
        toolTasks +=  pipelineSpecs["fileMover"]["additionalTasks"] 
    
    # set up all folders and links for each process
    for procIdx, fList in enumerate(processFrames):
            
        o = open(pipelineSpecs["fileMover"]["fileMoverProcessFile"].format(procIdx),"w+")
        c=[]

        # add for this process all tool tasks
        c += toolTasks
        
        # Set up all file move stuff for all frames (recover,dependend...)
        for fr in fList:
             for m in fr["fileMover"]:
                 c.append(m)
        cF.jsonDump(c,o,indent=4)
        o.close()
        
    
    print("Wrote file mover pre-process files for all ranks for local directory")  


def distributeFrames(opts,sortedFrames):
    
    totalFrames = len(sortedFrames)
    
    if totalFrames == 0:
        print("No frames to render! -> exit")
        return None
        
    nFramePerProc = int(totalFrames / opts.processes);
    frameCountPerProc = [nFramePerProc] * opts.processes;
    for i in range(0, (totalFrames - nFramePerProc*opts.processes)):
        frameCountPerProc[i] += 1;
    print("Frames per Process:"  + str(frameCountPerProc)) 
    processes = opts.processes - frameCountPerProc.count(0);
    print("Number of processes to use: %i" % processes)
    
    frames = sortedFrames;
    procFrames ={}; procIdx = 0;
    processFrames = [];    # the list of all procFrames dicts
    procFrames =  []       # for each processor -> [frames ,....]
    while( procIdx < processes):
        
        maxToTake = min( frameCountPerProc[procIdx] , len(frames) );
        
        # consume as many as possible
        procFrames +=  frames[0:maxToTake]
        del frames[0:maxToTake]
        
        frameCountPerProc[procIdx] -= maxToTake;

        # move to next process
        procIdx+=1;
        processFrames.append(procFrames)
        procFrames = []

    
    # check if all frames are empty in framesPerFile
    if(len(sortedFrames) != 0):
        raise NameError("Something went wrong with distributing frames over processes")
        
    # check if all frames have been distributed correctly
    total = sum([ len(procFrames) for procFrames in processFrames ])
    
    if(total != totalFrames):
        raise NameError("Something went wrong with distributing frames over processes")
    
    return processFrames

def recoverFrames(opts,allFrames,framesPerIdx, pipelineTools):
    
    
    def addFile(frame,file,parent=None):
        
        if "usedFile" in file and file["usedFile"] :
            #this file has already been used
            return
        
        if file["status"]==STATUS_RECOVER:
            
            print("added File: %s (recover)" % file["relPath"])
            # add a file move to recover this file
            frame["fileMover"].append(file["fileMoveRecover"])
            # mark file as used
            file["usedFile"] = True
            
        elif file["status"]==STATUS_FINISHED:
            if parent:
                print("added File: %s (finished, dependent)" % file["relPath"])
                # add a file move to recover this file
                frame["fileMover"].append(file["fileMoveDependent"])
                #print("id", id(frame), frame["fileMover"] )
                # mark file as used
                file["usedFile"] = True

    def addTool(frame,toolName, visitedTools,  parentToolName=None):        
        
       if toolName in visitedTools:
           return
           
       visitedTools.add(toolName);
       frameTool = frame["tools"][toolName]
       # if tool is not finished
       if frameTool["status"] != STATUS_FINISHED:    
           
            # add all this tools checkpoint files
            for outFileProp in frameTool["outputFiles"]:
                   
                if not outFileProp["cpFile"] == None:
                    addFile(frame,outFileProp["cpFile"],parentToolName)
          
            # add all dependent tools
            depTools = pipelineTools[toolName]["dependencies"]
            if depTools:
                for depTool in depTools:
                   addTool(frame,depTool,visitedTools,toolName)
                
       else:
            # we are finished, but
            # if we have a parent tool (always not finished), 
            # we add our finished checkpoint files
            if parentToolName:
               # add all its checkpoint files of output files
                for outFileProp in frameTool["outputFiles"]:
                   
                    if outFileProp["cpFile"] == None:
                        raise ValueError("""Trying to add non existant checkpoint file of output file %s in tool 
                        %s!""" % (str(outFileProp),toolName) )
                   
                    addFile(frame,outFileProp["cpFile"],parentToolName)
                   
            #else:
            # if no parent given, dont do anything

        
    
    # get all file info
    if opts.validationFileInfo:
        print("Setup recovery from file info===============================")
        print("Checkpoint files: %s", opts.validationFileInfo)
        checkpointFiles = cF.jsonLoad(opts.validationFileInfo);
        
        cpFiles = { "hash": {}, "all" : []}
        
        for f in checkpointFiles:
            tool = f["tool"]
            fileId = f["hash"]
            frameIdx = int(f["frameIdx"])
            ha = f["hash"]
            
            
            cpFiles["all"].append(f)
            
            if ha in cpFiles["hash"]:
                raise ValueError("File %s and %s have the same hash!" % (f["absPath"], cpFiles["hash"][ha]["absPath"] ) ) 
            else:
                cpFiles["hash"][ha] = f

        print("===========================================================")
        
        print("Determine status of all tools =============================")
        # move over all frames, for each tool and match cpFiles 
        for frameIdx,frame in framesPerIdx.items():
            finished = False;
            
            for toolName,tool in frame["tools"].items():
                
                # if there are checkpoint files corresponding to outputfiles of this tool
                finishedOutFiles = 0
                for outFileProp in tool["outputFiles"]:

                    ha =  cF.makeUUID(outFileProp["hashString"])
                    
                    
                    outFileProp["hash"] = ha
                    if ha in cpFiles["hash"]: # we found checkpoint file
                        cpFile = cpFiles["hash"][ha]
                        absP = cpFile["absPath"]
                        
                        print("Frame: %i " % frameIdx + 
                        " checkpoint file matched: %s , hash: %s, \n status: %s " % ( absP[:10]+'...'+absP[-20:] if len(absP) > 30 else absP ,ha, cpFile["status"] ))
                        
                        outFileProp["cpFile"] = cpFile
                        
                        if outFileProp["cpFile"]["status"] == STATUS_FINISHED:
                            finishedOutFiles += 1
                            
                    else:
                        outFileProp["cpFile"] = None
                    
                    
                    
                # if all output files are finished -> tool is finished
                if finishedOutFiles == len(tool["outputFiles"]):
                    
                    tool["status"] =  STATUS_FINISHED
                    print("Tool: %s -> finished" % toolName)
                
        
        #print("Dependency check===========================================")
        
        
        ## for each frameIdx file list, 
        ## travel dependency of each file and if some files are missing       
        ## silently remove this file from the cpFilesPerFrame because this frameIdx can not be recovered!
        
        #invalidFrameIdx = set() # list for not recoverable frames! (should not happen)
        #for frameIdx,frame in framesPerIdx.items():
            
            #if frameIdx not in cpFilesPerFrame:
                #continue
            #stack = cpFilesPerFrame[frameIdx]["all"][:] # shallow copy (remove files from stack)
            #invalidFrame = walkDependencies(stack,cpFilesPerFrame[frameIdx])
            
            #if invalidFrame:
                #print("Invalid frameIdx: %i for recovery!" % frameIdx)
                #invalidFrameIdx.add(frameIdx)
                ## continue to next frame
                #continue
        ##endfor
                
        ## remove all files from all tools for invalid frames
        #for k in invalidFrameIdx:
            #for toolName,tool in framesPerIdx[k].items():
                #if toolName in pipelineTools.keys():
                    #tool["checkpointFiles"] = []
                
        #print("===========================================================")
        
        
        # setup recovery for all frames
        print("Setup pipeline tools with file info ========================")
        for frame in allFrames:
            
            # walk all tools in pipeline (visit all once!)
            for tool in pipelineTools.keys():
               addTool(frame,tool,set())
                       

        print("===============================================================")

def main():
         
    
    parser = MyOptParser()

    parser.add_argument("--pipelineSpecs", dest="pipelineSpecs", default="" ,
            help="""Json file with info about the pipeline, fileValidation, fileValidationTools.""", metavar="<path>", required=True)    
    
    parser.add_argument("--validationFileInfo", dest="validationFileInfo", default="" ,
            help="""XML file with info about render output files.""", metavar="<path>", required=False)
                                                                
    parser.add_argument("-p", "--processes", type=int, dest="processes", default=int(1),
            help="The number of processes for the cluster render", metavar="<integer>", required=True)
    
            
    try:
        
        print("================== Prepare for Cluster Pipeline Job============")
        
        opts= AttrMap(vars(parser.parse_args()))
        
        pipelineSpecs = cF.jsonLoad(opts.pipelineSpecs)
        

        pipelineTools = pipelineSpecs["pipelineTools"]
        
        # define parents and dependencies for all tools
        for toolName,tool in pipelineTools.items():
            if "dependencies" not in tool:
                tool["dependencies"]=set()
            
            tool["parents"]=set()
            
        for toolName,tool in pipelineTools.items():
            for dep in tool["dependencies"]:
                t = pipelineTools[dep]
                t["parents"].add(toolName)

        
        frameGenerator = pipelineSpecs["frameGenerator"]
#        fileValidationSpecs = d["fileValidationSpecs"]
#        fileValidationTools = d["fileValidationTools"]
        
        # Important job modules to hand over to frameGenerators and processFileWriters
        importantModules = {"importHelpers":iH, "commonFunctions" : cF, "getSimFileInfos" : getSimFileInfos}
        
        # Generate Frames =====================================================
        mod, frameGenerator["generator"] = iH.importClassFromModuleString(frameGenerator["generator"])
        # hand over some modules to the frame generator!
        fgen = frameGenerator["generator"](pipelineSpecs, jobGenModules =  importantModules )
        allFrames,framesPerIdx, framesToDistribute = fgen(**frameGenerator["arguments"])
        # =====================================================================
        
            
        # Formatting frames ========================================================
        # format strings in all settings (if possible) in allFrames again with itself     
        for i,fr in enumerate(allFrames):
            allFrames[i] = cF.formatAll(fr,fr,formatter=StrExpr)
        
        # Filter Frames =======================================================
        recoverFrames(opts,allFrames,framesPerIdx,pipelineTools)
        #======================================================================
                  
        # remove all frames which are completely finished (all tools with no parents are finished, means completely finished)
        notcompleted = lambda frame:   sum( 1 if frame["tools"][toolName]["status"] != STATUS_FINISHED 
                                                else 0 for toolName,tool in pipelineTools.items() if len(tool["parents"])==0 ) > 0
        framesCount = len(allFrames);
        allFrames = list(filter(notcompleted, allFrames))
        framesToDistribute = list(filter(notcompleted, framesToDistribute))
        print("Removed %d finished frames!" % (framesCount - len(allFrames)) )
        
        
    
            
        
        #count number of frames to render
        totalFrames = len(framesToDistribute);
        print("Number of frames to compute %i" % totalFrames)
        if(totalFrames == 0):
          print("No frames to distribute -> exit")
          return 0
        
        # Distribute the processes over the number of processes ===============
        processFrames = distributeFrames(opts,framesToDistribute)
        #======================================================================

        
        # Write for each tool in the pipeline the process file, for each process a seperate one
        for toolName,tool in pipelineTools.items():
            
            # load the class and module for the tools processFileWriter
            print("Load processFileGenerator for tool: %s" % toolName )
            mod, tool["processFileGenerator"]["generator"] = iH.importClassFromModuleString(tool["processFileGenerator"]["generator"])
            tool["processFileGenerator"]["generator"](pipelineSpecs, jobGenModules = importantModules).write(processFrames, **tool["processFileGenerator"]["arguments"])
            
            # if we have some info file generator , produce the output
            
            if "infoFileGenerator" in tool:
                print("Load infoFileGenerator for tool: %s" % toolName )
                mod, tool["infoFileGenerator"]["generator"] = iH.importClassFromModuleString(tool["infoFileGenerator"]["generator"])
                tool["infoFileGenerator"]["generator"](pipelineSpecs, jobGenModules = importantModules).write(processFrames, **tool["infoFileGenerator"]["arguments"])
            
        
        # Write FileMover process file  =======================================
        writeFileMoverProcessFile(pipelineSpecs,processFrames)
        # =====================================================================
        return 0
         
    except Exception as e:
        print("====================================================================")
        print("Exception occured: " + str(e))
        print("====================================================================")
        traceback.print_exc(file=sys.stdout)
        parser.print_help()
        return 1

if __name__ == "__main__":
   sys.exit(main());