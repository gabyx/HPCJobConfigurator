# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os,copy
import ast
from HPCJobConfigurator.jobGenerators.importHelpers import ImportHelpers as iH
from HPCJobConfigurator.jobGenerators.commonFunctions import CommonFunctions as cf
from HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generator import GeneratorMPI



class ToolPipeline(GeneratorMPI):
    
    # automatic generated options which are not interpolated till the end
    nonInterpolatedOptions = {"Pipeline" : set()}     
    
    def __init__(self,clusterOptions):
        super(ToolPipeline,self).__init__(clusterOptions , ToolPipeline.nonInterpolatedOptions );
        self.cPipeline = None
        
    def convertValues(self):
       super(ToolPipeline,self).convertValues();         
       self.__convertValues()
    
    def checkConfig(self, interact = True):
       super(ToolPipeline,self).checkConfig(interact);         
       self.__checkConfig(interact)
       
    def __convertValues(self):
        self.cPipeline = self.configDict["Pipeline"]
        
        
    def __checkConfig(self,interact):
        pass
    
    def printOptions(self):
        super(ToolPipeline,self).printOptions();
        
    def generate(self):
        

        configDicts = [None]        
        
        if self.cCluster.jobIdxParent >= self.cCluster.nJobs-1:
            raise ValueError("jobIdxParent=%i not feasible, since you generate %i jobs from idx 0 till %i !" % (self.cCluster.jobIdxParent,self.cCluster.nJobs, self.cCluster.nJobs-1) )
        for jobIdx in range(0,self.cCluster.nJobs):
            
            print("Generating MPI Job: Simulation Render =================")
            print("-> JobIndex: %i" % jobIdx + (" (no generating, because parent job!)" if jobIdx <= self.cCluster.jobIdxParent else "") )
            
            # first make a new self.config
            self.config = self.makeInterpolationConfig();

            # setting the jobIdx
            self.config["Job"]["jobIdx"] = str(jobIdx)
            
            self.config["Job"]["submitCommand"] = " ".join([self.config["Cluster"]["submitCommand"] , 
                        (configDicts[-1].Cluster.submitArgsChainJob if jobIdx != 0 else "") , self.config["Job"]["submitArgs"]])
            


            if configDicts[-1]:
                self.config["Pipeline-PreProcess"]["validationInfoFile"] = configDicts[-1]["Pipeline-PostProcess"]["validationInfoFile"]
            else:
                self.config["Pipeline-PreProcess"]["validationInfoFile"] = ""
            
            # final interpolation of all automatic generated options and conversion to self.configDict
            # and checking of feasible values before template writting
            # from now self.cCluster , self.cJob and self.cRigidBodySim are available (reference to self.configDict)
            self.convertValues()

            
            # only make jobs which are greater then parent!
            if jobIdx > self.cCluster.jobIdxParent:
                
                self.checkConfig(interact=self.cCluster.interact)
                self.printOptions()
                
                # make job script dir (if exists, try to remove it, if no -> abort)
                cf.makeDirectory( self.cJob.scriptDir, name="Job script dir", defaultMakeEmpty=False, interact= self.cCluster.interact)
                
                self.writeJobScriptArgs( os.path.join(self.cJob.scriptDir, "submitScriptArgs.txt" ) )
                
                # write all templates
                self.writeTemplates(self, configDicts);

                # check if we submit command
                # overwrite submit command by appending all submit args 
                
                if self.cCluster.submitJobs:
                    print("Trying to submit job with command: \n%s" % self.cJob.submitCommand)
                    cf.callProcess(self.cJob.submitCommand)

        
            # save conficDict for next jobIdx (possibly)
            # TODO save config dict in job script folder (json file)            
            configDicts.append(self.configDict)
            
            print("==========================================================")
        
        
        # Write total submit file to first folder 
        config0 = configDicts[self.cCluster.jobIdxParent+2];
        filePath = os.path.join(config0.Job.scriptDir,"submitAll.sh")
        f = open(filePath,"w+")
        commands = [];        
        for c in configDicts:
            if c:
                commands.append(c.Job.submitCommand)
        
        f.write("\n".join(commands))       
        cf.makeExecutable(filePath);        
