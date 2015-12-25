# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import sys,os, subprocess,traceback,shutil, time
from attrdict import AttrMap

from subprocess import CalledProcessError

class AccivCorrelator:
    
    outputFolder = "./output"
    frameFolderTempl = os.path.join(outputFolder,"Frame-%04d")
    passFolderTempl  = os.path.join("pass%i")
    
    passLog = "accivCorrelator.log"
    
    def __init__(self, processFile, jobGenModules = None):
        
        self.processFile = AttrMap(processFile)
        
        self.pS = self.processFile.processSettings
        self.cS = self.pS.correlatorSettings
        
        self.plotS = self.pS.correlatorPlotClasses
        
        # import all plot classes
        self.iH = jobGenModules["importHelpers"]
        self.plotModules = []
        for i, importSettings in enumerate(self.plotS):
            mod, cl = self.iH.importClassFromModule(modulePath=importSettings["modulePath"],
                                                          moduleName=importSettings["moduleName"],
                                                          className=importSettings["className"])
                                                          
            options = importSettings["options"] if "options" in importSettings else dict()
            self.plotModules.append((cl,importSettings["options"]))
            
        self.fr = self.processFile.frames
        
    def doProcessing(self):
        
        print("============ AccivCorrelator: Correlate Frames  =========")
        
        self.origWD = os.getcwd() 
        
        self.filesToDelete = set()
        for frame in self.fr:
            start = time.time()
            self._processFrame(frame)
            stop = time.time()
            print("Correlation for frameIdx: %i took %d seconds" % (frame.frameIdx,stop-start) )

        # delete all collected files
        print("Delete all files in the deleter list")
        for f in self.filesToDelete:
            print("Delete file %s" % f )
            os.remove(f)
        
        print("=============== AccivCorrelator:  finished ==============")
    
    def _resolveFile(self,fi,searchPaths):
        if os.path.isabs(fi):
            raise ValueError("Path %s should be a relative path for search paths %s" % (fi,str(searchPaths)))
            
        for p in searchPaths:
            res = os.path.join(p,fi)
            if os.path.exists(res):
                return os.path.realpath(res)
                
        raise ValueError("Path %s could not be resolved with search paths %s" % (fi,str(searchPaths)) )
    
    def _processFrame(self,frame):
        
        print("Correlation for frameIdx: %i" % frame.frameIdx)
        
        
        # make frame folder
        frameFolder = os.path.join(AccivCorrelator.frameFolderTempl % frame.frameIdx)
        os.makedirs(frameFolder,exist_ok=False)
        
        # copy parameter file to frame folder
        shutil.copy( self.cS.defaultParameterFile, os.path.join( frameFolder, "defaultParameters.ascii" ) )
        
        if self.cS.passes <=0:
            raise ValueError("We need at least 1 pass, but %i passes was specified" %self.cS.passes)
        
        if len(self.cS.parameterFiles) < self.cS.passes :
            raise ValueError("To little parameter files: %s for %i passes!" % (str(self.cS.parameterFiles),self.cS.passes))
        
        
        
        passFolders = []
        for passIdx in range(0,self.cS.passes):
            print("Setup passes %i" % (passIdx+1))
            
            passFolder =  os.path.join( frameFolder, AccivCorrelator.passFolderTempl % (passIdx+1) )
            os.makedirs(passFolder,exist_ok=False)
            
            #copy parameter file to pass folder
            shutil.copy( self.cS.parameterFiles[passIdx], os.path.join( passFolder, "parameters.ascii" ) )
            passFolders.append(passFolder)
            
        print("Setup images")
        if len(frame.inputFiles) == 0:
            raise ValueError("No input images")
            
        images = []
        imageLinks =[]
        # make image links re-enumerated from zero (image-0.h5, image-1.h5 , .... ) in frame folder
        for fIdx, f in enumerate(frame.inputFiles):
            # resolve image
            resolvedPath =  self._resolveFile( f, self.cS.imageSearchPaths )
            images.append(resolvedPath)
            
            # make link to new file in frame folder,
            linkPath =  os.path.join( frameFolder , self.cS.accivImageNameFormat % fIdx )
            
            os.symlink(resolvedPath,linkPath)
            print("Linked file %s ---> %s " % (resolvedPath,linkPath) )
            imageLinks.append(linkPath)
        
        # check if geometry factor file is present (built file relative to first pass folder)
        geometryFile = os.path.join(passFolders[0], self.cS.accivGeometryFactorsFile)
        if not os.path.exists(geometryFile):
            print("Build Geometry Factors")
            command = self.cS.preExecutable.split(" ") + [ images[0], geometryFile, "flat" ]
            try:
                out = subprocess.check_output(command)
            except CalledProcessError as c:
                raise ValueError("Building geometry factors failed! %s, output: %s" % (command,c.output) )


        for passIdx, passF in enumerate(passFolders): 
            
            print("Start Acciv Pass: %s" % passF)
            
            command = self.cS.executable.split(" ") + [passF]
            print("Command: %s" % str(" ".join(command)))
            try:
                logPath=os.path.join(passF,AccivCorrelator.passLog)
                with open(logPath,"w") as log:
                    subprocess.check_call(command, stdout = log, stderr=subprocess.STDOUT )
            except CalledProcessError as c:
                print("Acciv process error: for file: %s --> see log: %s" % (f,logPath) )
                print("Continue to next frame ...")
        
            
            # plot results
            print("Start plotting: %s" % passF )
            for plotter, options in self.plotModules:
                options.update({"folder": passF, "imageFileName": images[0], "frameIdx" : frame.frameIdx })
                plotter(options)
                
            # cleanup pass (with command , format with pass folder)
            
            if self.cS.passCleanUpCommand :
                cmd = self.cS.passCleanUpCommand % passF
                print("Clean up pass with command: %s" % cmd)
                try:
                    subprocess.check_call(cmd, shell=True)
                except CalledProcessError as c:
                    print("Cleanup acciv pass error!")
                    print("Continue to next frame ...")
            
        # delete all links for this frame
        # delete all real images, keep only first image
        print("Start plotting: %s" % passF )
        for l in imageLinks:
            print("Remove link: %s" % l )
            os.remove(l)
          
        # keep only first image, delete the others
        # if first image is alread in deleter list, take it out of it!
        if images[0] in self.filesToDelete:
          print("Removed iamge %s from deleted list" % images[0]) 
          self.filesToDelete.remove(images[0])
          
        for i in range(1,len(images)):
            print("Add image to remove: %s" % images[i] )
            self.filesToDelete.add(images[i])
        
        stop = time.time()
        
        # flush standart out
        sys.stdout.flush()