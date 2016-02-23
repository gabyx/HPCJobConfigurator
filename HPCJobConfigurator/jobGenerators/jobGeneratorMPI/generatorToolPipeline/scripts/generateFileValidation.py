# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================



import sys
if sys.version_info[0] != 3:
    print("This script is only python3 compatible!")
    exit(1)

import os, subprocess, ctypes,re,traceback,ast,copy
import json, glob2


from argparse import ArgumentParser
from attrdict import AttrMap
import xml.etree.ElementTree as ET

from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF



class MyOptParser(ArgumentParser):
    def error(self,msg):
        self.print_help()
        raise ValueError("Error occured: " + msg)



def validateFile(validationCommands,fileList):
    valid = []
    if not isinstance(fileList,list):
        fileList = list(fileList)
        
    for f in fileList:
        ext = os.path.splitext(f)[1]
        if ext in validationCommand:
            command += validationCommand[ext] + " %s" % f
            try:
                cF.callProcess(command)
                valid.append(True)
            except subprocess.CalledProcessError: 
                valid.append(False)
        else:
            valid.append(False)
                     
    return valid

def searchFiles(searchDir,opts,fileValidationSpecs,fileValidationTools,pipelineTools):
    # compile all regexes
    regexes = {}
    for i,spec in enumerate(fileValidationSpecs):
        try:
            regexes[i] = re.compile(spec["regex"])
        except:
            raise ValueError("Could not compile regex: %s" % spec["regex"])
        
    allFiles = {}
    filesPerProc = {}
    # walk directory and 
    for dirpath, dirs, files in os.walk(searchDir,followlinks=True):

        for file in files:
            
            filePath = os.path.realpath(os.path.join(dirpath, file))
            #print(os.path.join(dirpath, file))
            # try to match path with all regexes till one matches:
            for specIdx, spec in enumerate(fileValidationSpecs):
                
                m=regexes[specIdx].search(filePath)
                
                # we have a file match
                if m:
                    
                    try:
                        processId = int(m.group("processId"))                
                    except:
                        raise ValueError("Non convertable processId found in filePath %s" % filePath)  
                    
                    if processId not in filesPerProc:
                        filesPerProc[processId] = {"allFiles" : [] , "tools" : { tool:[] for tool in pipelineTools.keys() } };
                    
                    #make dict for this file
                    f = {}
                    # add regex groups
                    f.update(m.groupdict())

                    # add all values from the validation spec (deep copy since we want for each one a different)
                    f.update(copy.deepcopy(spec))
                    
                    # set file status on finished, (as initial guess, validation fully determines this value)
                    f.update({"status":"finished"})                            
                    
                    # format all values again with the regex results
                    f = cF.formatAll(f,m.groupdict(),exceptKeys={"regex":None})

                    # get tool of this file
                    if "tool" in f:
                        tool = f["tool"]    
                        if tool not in pipelineTools.keys():
                            raise ValueError("The tool %s is not in %s!" % (tool,str(pipelineTools.keys())) )
                    else:
                        raise ValueError("You need to define a 'tool' key for %s " % str(spec))
                        
                    # make hashes
                    if "hashString" in spec:
                        h = cF.makeUUID( spec["hashString"].format(**m.groupdict()) )
                        f["hash"] = h
                    else:
                        raise ValueError("You need to define a 'hash' key for file %s " % str(spec))
                        
                        
                    # convert frameIdx
                    if "frameIdx" in f:
                         f["frameIdx"] = int(f["frameIdx"])
                    else:
                         raise ValueError("You need to define a 'frameIdx' key for %s (or in regex!) " % str(spec))                            
                    
                    # add file to the lists
                    filesPerProc[processId]["allFiles"].append( f )
                    filesPerProc[processId]["tools"][ tool ].append(f)
                    
                    
                    if f["hash"] not in allFiles:
                            allFiles[f["hash"]] = f
                    else:
                        raise ValueError("Found files with the same hash %s, %s, this should not happen!" % (f["absPath"], allFiles[f["hash"]]["absPath"] ) )
                    
                    
                    break
                        
    if not allFiles:
        print("We found no files in folder: %s to validate!" % searchDir) 
        return allFiles          
     
    # sort files according to maximal modified time of the output files for each tool and each process
    for procId, procFiles in filesPerProc.items():
        for tool,files in procFiles["tools"].items():
            filesPerProc[procId]["tools"][tool] =  sorted( files , key= lambda file : os.path.getmtime(file["absPath"]) );

    #determine files to validate
    filesToValidate = []
    for procid, procFiles in filesPerProc.items():
            if opts.validateOnlyLastModified:
               # validate last file of all tools for each processor, to see if its ok or not, all others are valid
               for tool, toolFiles in procFiles["tools"].items():
                   if toolFiles:
                       filesToValidate.append(toolFiles[-1])
            else:
               filesToValidate += procFiles["allFiles"]

      
    # Validate all files with the appropriate command

    for fIdx, file in enumerate(filesToValidate):
        try:
            ext = os.path.splitext(file["absPath"])[1];
            try:
                validateCmd = fileValidationTools[ext]
            except:
                print("No validation command found for extentsion of file: %s" % file["absPath"])
                raise
            

            validateCmd = validateCmd.format(**{"file":file["absPath"]})

            try:
                out = subprocess.check_output(validateCmd.split(" ")).decode('utf-8')
            except:
                print("Validation command %s failed!" % validateCmd)
                raise
                
            if out not in ["finished","recover"]:
                print("Validation output %s not in list ['finished','recover']" % out)
                raise
            else:
                validationAttributes = {"status":out}
                
            filesToValidate[fIdx].update(validationAttributes);
        except:

            # file is invalid, clear this file from the list 
            filesToValidate[fIdx]["status"] = "invalid";

    print("Validated last files of each tool in the pipeline: ", "\n".join([ f["absPath"] + " --> " + f["status"] for f in filesToValidate ]) ) 

    # filter all empty stuff from lists:
    allFiles = dict(filter(lambda x : x[1]["status"] != "invalid" ,allFiles.items()))
    del filesPerProc
    return allFiles

def loadValidationFiles(globExpr):
  files = glob2.glob(globExpr)
  if not files:
    print("WARNING: No validation file infos found with globbing expression: '%s'" % globExpr)
  else:
    print("Found %i validation files" % len(files))
    
  valFiles = []
  valDataAll = {}
  for f in files:
      data = json.load(open(f))
      valFiles.append( { "path": f , "valData" : data } )
      
      for fileInfo in data:
        fileInfo["validatationInfoPath"] = os.path.abspath(f)
        h = fileInfo["hash"]
        if h not in valDataAll:
          valDataAll[h] = fileInfo
        else:
          raise NameError("FileInfo: %s already added to data set of all validation files: %s " % (fileInfo, files) )
          
  return valDataAll, valFiles

def printSummary(finalFiles, pipelineTools, printDetails=False):

    tools=dict( [ (tool,{"finished": 0, "recover" : 0}) for tool in pipelineTools.keys() ] )
    
    print("Validatation summary ===============")
    for f in finalFiles:
        if printDetails:
            print("File: %s, status: %s" % (f["absPath"],f["status"]))
        
        t = f["tool"]
        if f["status"] == "finished":
            tools[t]["finished"] += 1
        elif f["status"] == "recover":
            tools[t]["recover"] += 1
            
    for t,count in tools.items():
        print("Tool: %s, file count: \n\tfinished: %i\n\trecover: %i" % (t, count["finished"], count["recover"]))
        
    print("====================================")  
           
def preferGlobalPaths(valDataAll):
    """ The absPath might point to an inexistent file, replace by globalPath """
    for valInfo in valDataAll.values():
      absExists = os.path.exists(valInfo["absPath"])
      if "globalPath" in valInfo:
          globExists = os.path.exists(valInfo["globalPath"])
          if globExists:
              valInfo["absPath"] = valInfo["globalPath"]
          elif absExists:
              print("""WARNING: existing absPath: %s not replaced by inexistent globalPath %s """ % valInfo["globalPath"])
      else:
          if not absExists:
              raise ValueError("You need to provide a globalPath in the file info! absPath %s not existing!" % valInfo["absPath"])
      

def main():
    
    """ {old validatation file infos}  is compared 
        to { new validation file infos}  ==> outputs new file validation info
    """
    
    parser = MyOptParser()
    
    parser.add_argument("-s", "--searchDirNew", dest="searchDirNew",
            help="""This is the search directory where it is looked for output files (.tiff,.exr,.rib.gz). """, 
            metavar="<path>", default=None, required=False)
    
    
    parser.add_argument("--valFileInfoGlobNew", dest="valFileInfoGlobNew",
            help="""
            The globbing expression for all input xmls with file status which 
            are consolidated into a new file info under --output. The found and validated files in --searchDir (if specified) are
            added to the set of new files.
            """, default=None, metavar="<glob>", required=False)
    
    parser.add_argument("--valFileInfoGlobOld", dest="valFileInfoGlobOld",
            help="""
            The globbing expression for all old input xmls with file status which 
            are consolidated with the new files into a combined file info under --output.
            """, default=None, metavar="<glob>", required=False)
    
    parser.add_argument("--pipelineSpecs", dest="pipelineSpecs", default="",
            help="""Json file with info about the pipeline, fileValidation, fileValidationTools.                 
                 """, metavar="<string>", required=True)
    
    parser.add_argument("--statusFolder", dest="statusFolder", default=None,
            help="""The output status folder which contains links to files which are finished, or can be recovered.                
                 """, metavar="<string>", required=False)
    
                                                       
    parser.add_argument("--validateOnlyLastModified", dest="validateOnlyLastModified", type=cF.toBool, default=True,
            help="""The file with the moset recent modified time is only validated, all others are set to finished!.""", required=False)
                         

    parser.add_argument("-o", "--output", dest="output",
            help="""The output xml which is written, which proivides validation info for each file found""", metavar="<path>", required=True)
    
    
    try:
        
        print("====================== FileValidation ===========================")
        
        opts= AttrMap(vars(parser.parse_args()))
        if not opts.searchDirNew and not opts.valFileInfoGlobNew:
            raise ValueError("You need to define either searchDirNew or valFileInfoGlobNew!")
        
        if opts.valFileInfoGlobOld == "":
            opts.valFileInfoGlobOld = None
        
        print("searchDir: %s" % opts.searchDirNew)
        print("valFileInfoGlobNew: %s" % opts.valFileInfoGlobNew)
        print("valFileInfoGlobOld: %s" % opts.valFileInfoGlobOld)
        print("output: %s" % opts.output)
        
        
        d = cF.jsonLoad(opts.pipelineSpecs)
        pipelineTools = d["pipelineTools"]
        fileValidationSpecs = d["fileValidationSpecs"]
        fileValidationTools = d["fileValidationTools"]
        
        valDataAllNew = dict()
        deleteFiles = []
        
        # load new validataion datas
        if opts.valFileInfoGlobNew is not None:
            print("Load new validation files")
            valDataAllNew , valFilesNew  = loadValidationFiles(opts.valFileInfoGlobNew)
            
            preferGlobalPaths(valDataAllNew)
            
        
        # add searchDir files to new set
        # search files ============================================================================
        if opts.searchDirNew is not None:
            print("Validate all files in: %s with pipeLineSpecs: %s" % (opts.searchDirNew , opts.pipelineSpecs) )
            allFiles = searchFiles(opts.searchDirNew, opts, fileValidationSpecs,fileValidationTools,pipelineTools)
            for ha, f in allFiles.items():
              if ha in valDataAllNew:
                  print("""WARNING: File %s already found in validation data set 
                           from globbing expr. %s """ % (f["absPath"], opts.valFileInfoGlobNew))
              else:
                valDataAllNew[ha] = f
        # ===============================================================================================
        
        
        
        # load old validation datas
        if opts.valFileInfoGlobOld is not None:
            print("Load old validation files")
            valDataAllOld , valFilesOld  = loadValidationFiles(opts.valFileInfoGlobOld)
            preferGlobalPaths(valDataAllOld)
            
            # add old to new validatation infos 
            for ha, valInfo in valDataAllOld.items():
              
                if ha not in valDataAllNew:
                    # this old file hash is not in our current list, so add it!
                    
                    # check absPath if it exists otherwise try to extent the relPath with dir of this validation file.
                    if not os.path.exists(valInfo["absPath"]):
                      absPath = os.path.join( os.path.dirname(valInfo["validatationInfoPath"]) , valInfo["relPath"] )
                      if not os.path.exists(absPath):
                         print(valInfo["validatationInfoPath"])
                         raise NameError("""File path in valid. info file: %s 
                                            does not exist, extended rel. path to: %s does also not exist!""" % (valInfo["absPath"],absPath))
                      else:
                         print("Replacing inexisting path %s with %s", valInfo["absPath"], absPath)
                         valInfo["absPath"] = absPath
                      
                    # copy element to new file info
                    valDataAllNew[ha] = valInfo
                else:
                    # we have the same hash in the new info
                    # take our new one which is better!
                    # delete old file if it is not linked to by new file

                    if  os.path.realpath(valDataAllNew[ha]["absPath"]) !=  os.path.realpath(valInfo["absPath"]):
                        deleteFiles.append(valInfo["absPath"])
     

        # make final list
        finalFiles = [ f for f in valDataAllNew.values() ]
        
        printSummary(finalFiles,pipelineTools,False)
        
        print("Make output validation file")
        f = open(opts.output,"w+")
        cF.jsonDump(finalFiles,f, sort_keys=True)
        f.close();
        
        # Renew status folder, move over new xml info
        if opts.statusFolder is not None:
          
            print("Renew status folder:")
            finished = os.path.join(opts.statusFolder,"finished")
            recover = os.path.join(opts.statusFolder,"recover")
            
            cF.makeDirectory(finished,interact=False, defaultMakeEmpty=True)
            cF.makeDirectory(recover ,interact=False, defaultMakeEmpty=True)
            # make symlinks for all files in the appropriate folder:
            paths = {"recover": recover, "finished": finished}           
            
            for f in finalFiles:
                h = f["hash"]
                p = os.path.relpath(f["absPath"],start=paths[f["status"]])
                filename = os.path.basename(p)
                head,ext = os.path.splitext(filename)
                
                os.symlink(p, os.path.join( paths[f["status"]] , head+"-uuid-"+h+ext ) );


        print("=================================================================")
        
    except Exception as e:
        print("====================================================================")
        print("Exception occured: " + str(e))
        print("====================================================================")
        traceback.print_exc(file=sys.stdout)
        parser.print_help()
        return 1

if __name__ == "__main__":
   sys.exit(main());
