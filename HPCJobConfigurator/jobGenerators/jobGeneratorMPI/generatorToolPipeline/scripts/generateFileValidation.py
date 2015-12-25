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
import json


from argparse import ArgumentParser
from attrdict import AttrMap
import xml.etree.ElementTree as ET

from HPCJobConfigurator.jobGenerators.importHelpers import ImportHelpers as iH
from HPCJobConfigurator.jobGenerators.commonFunctions import CommonFunctions as cf



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
                cf.callProcess(command)
                valid.append(True)
            except subprocess.CalledProcessError: 
                valid.append(False)
        else:
            valid.append(False)
                     
    return valid
   
def main():
         
    
    parser = MyOptParser()
    
    parser.add_argument("-s", "--searchDir", dest="searchDir",
            help="""This is the search directory where it is looked for render output files (.tiff,.exr,.rib.gz). """, metavar="<path>", required=True)
    
    parser.add_argument("--pipelineSpecs", dest="pipelineSpecs", default="",
            help="""Json file with info about the pipeline, fileValidation, fileValidationTools.                 
                 """, metavar="<string>", required=True)
    
    parser.add_argument("--statusFolder", dest="statusFolder", default="",
            help="""The output status folder which contains links to files which are finished, or can be recovered.                
                 """, metavar="<string>", required=False)
    
                                                       
    parser.add_argument("--validateOnlyLastModified", dest="validateOnlyLastModified", type=cf.toBool, default=True,
            help="""The file with the moset recent modified time is only validated, all others are set to finished!.""", required=False)
                    
    parser.add_argument("-v", "--validationFileInfo", dest="validationFileInfo",
            help="""The input xml with file status which is updated and a new info is saved under --output.""", default="", metavar="<path>", required=False)                
    
    parser.add_argument("-o", "--output", dest="output",
            help="""The output xml which is written, which proivides validation info for each file found""", metavar="<path>", required=True)
    
    
    try:
        
        print("================== FileValidation ==================== ")
        
        
        opts= AttrMap(vars(parser.parse_args()))
        
        print("validationInput: %s" % opts.validationFileInfo)
        print("validationOutput: %s" % opts.output)
        
        
        d = cf.jsonLoad(opts.pipelineSpecs)
        pipelineTools = d["pipelineTools"]
        fileValidationSpecs = d["fileValidationSpecs"]
        fileValidationTools = d["fileValidationTools"]
        
        # compile all regexes
        regexes = {}
        for i,specs in enumerate(fileValidationSpecs):
            try:
                regexes[i] = re.compile(specs["regex"])
            except:
                raise ValueError("Could not compile regex: %s" % specs["regex"])
            
        allFiles = []
        allFilesHash = {} 
        filesPerProc = {}
        # walk directory and 
        for dirpath, dirs, files in os.walk(opts.searchDir,followlinks=True):

            for file in files:
                
                filePath = os.path.join(dirpath, file) 
                # try to match path with all regexes till one matches:
                for specIdx, specs in enumerate(fileValidationSpecs):
                    
                    m=regexes[specIdx].search(filePath)
                    
                    # we have a file match
                    if m:
                        
                        try:
                            processId = int(m.group("processId"))                
                        except:
                            raise ValueError("Non convertable processId found in filePath %s" % filePath)  
                        
                        if processId not in filesPerProc:
                            filesPerProc[processId] = {"all" : [] , "tool" : { tool:[] for tool in pipelineTools.keys() } };
                        
                        #make dict for this file
                        f = {}
                        # add regex groups
                        f.update(m.groupdict())

                        # add all values from d (deep copy since we want for each one a different)
                        f.update(copy.deepcopy(specs))
                        
                        # set file status on finished, (as initial guess, validation fully determines this value)
                        f.update({"status":"finished"})                            
                        
                        # format all values again with the regex results
                        f = cf.formatAll(f,m.groupdict(),exceptKeys={"regex":None})

                        # get tool of this file
                        if "tool" in f:
                            tool = f["tool"]    
                            if tool not in pipelineTools.keys():
                                raise ValueError("The tool %s is not in %s!" % (tool,str(pipelineTools.keys())) )
                        else:
                            raise ValueError("You need to define a 'tool' key for %s " % str(specs))
                            
                        # make hashes
                        if "hashString" in specs:
                            h = cf.makeUUID( specs["hashString"].format(**m.groupdict()) )
                            f["hash"] = h
                            if h not in allFilesHash:
                                allFilesHash[h] = f
                            else:
                                raise ValueError("Found files with the same hash %s, %s, this should not happen!" % (f["absPath"], allFilesHash[h]["absPath"] ) )
                        else:
                            raise ValueError("You need to define a 'hash' key for file %s " % str(specs))
                            
                            
                        # convert frameIdx
                        if "frameIdx" in f:
                             f["frameIdx"] = int(f["frameIdx"])
                        else:
                             raise ValueError("You need to define a 'frameIdx' key for %s (or in regex!) " % str(specs))                            
                        
                        # add file to the lists
                        filesPerProc[processId]["all"].append( f )
                        filesPerProc[processId]["tool"][ tool ].append(f)
                            
                        allFiles.append(f)
                        
                        break
                            
        if not allFiles:
            print("We found no files in folder: %s to validate!" % opts.searchDir)            
            return 0
         
        # sort files according to maximal modified time of the output files for each tool and each process
        for procId, procFiles in filesPerProc.items():
            for tool,files in procFiles["tool"].items():
                filesPerProc[procId]["tool"][tool] =  sorted( files , key= lambda file : os.path.getmtime(file["absPath"]) );

        #determine files to validate
        filesToValidate = []
        for procid, procFiles in filesPerProc.items():
                if opts.validateOnlyLastModified:
                   # validate last file of all tools for each processor, to see if its ok or not, all others are valid
                   for tool, toolFiles in procFiles["tool"].items():
                       if toolFiles:
                           filesToValidate.append(toolFiles[-1])
                else:
                   filesToValidate += procFiles["all"]
        
          
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
        
        print("Validated files: ", "\n".join([ f["absPath"] + " --> " + f["status"] for f in filesToValidate ]) ) 
        
        
        # filter all empty stuff from lists:
        allFiles = list(filter(lambda x: x["status"] != "invalid" ,allFiles))
        allFilesHash = dict(filter(lambda pair: pair[1]["status"] != "invalid", allFilesHash.items()))
        del filesPerProc
        
                
     
        # compare with old fileInfo if we have one and update necessary files
        
        finalFiles = []        
        deleteFiles = []
        
        if opts.validationFileInfo:
            f = open(opts.validationFileInfo)
            oldFileInfo = json.load(f)
            
            for oldFile in oldFileInfo:
                h = oldFile["hash"] 
                if h not in allFilesHash:
                    # copy element to new file info
                    finalFiles.append(oldFile)
                else:
                    # we have the same hash in the new info
                    # take our new one which is better!
                    # added afterwards
                    newFile = allFilesHash[h]

                    # TODO, symbolic link and so on
                    # old one can be moved on the delete list                    
                    # if the new file is no symbolic link to the old file (hardlinks does not matter!)
                    if not os.path.islink(newFile["absPath"]):
                        deleteFiles.append(oldFile)
     

        # write out all our produced files which 
        for h,file in allFilesHash.items():
            finalFiles.append(file)
        
                
        f = open(opts.output,"w+")
        cf.jsonDump(finalFiles,f,indent=4, sort_keys=True)
        f.close();
        
        # Renew status folder, move over new xml info
        if opts.statusFolder:
            
            finished = os.path.join(opts.statusFolder,"finished")
            recover = os.path.join(opts.statusFolder,"recover")
            
            cf.makeDirectory(finished,interact=False, defaultMakeEmpty=True)
            cf.makeDirectory(recover ,interact=False, defaultMakeEmpty=True)
            # make symlinks for all files in the apropriate folder:
            paths = {"recover": recover, "finished": finished}           
            
            for f in finalFiles:
                h = f["hash"]
                p = os.path.relpath(f["absPath"],start=finished)
                filename = os.path.basename(p)
                head,ext = os.path.splitext(filename)
                
                os.symlink(p, os.path.join( paths[f["status"]] , head+"-uuid-"+h+ext ) );


        print("============================================================ ")
        
    except Exception as e:
        print("====================================================================")
        print("Exception occured: " + str(e))
        print("====================================================================")
        traceback.print_exc(file=sys.stdout)
        parser.print_help()
        return 1

if __name__ == "__main__":
   sys.exit(main());
