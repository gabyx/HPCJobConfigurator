# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os

from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF
from HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generator import GeneratorMPI
from HPCJobConfigurator.jobGenerators import configuratorExceptions as CE


class RigidBodySim(GeneratorMPI):
    
    # automatic generated options which are not interpolated till the end
    nonInterpolatedOptions = {"Job" : set(["sceneFile"])}     
    
    def __init__(self,clusterOptions):
        super(RigidBodySim,self).__init__(clusterOptions , RigidBodySim.nonInterpolatedOptions );
        self.cRigidBody = None
        
    def convertValues(self):
       super(RigidBodySim,self).convertValues();         
       self.__convertValues()
    
    def checkConfig(self,interact = True):
       super(RigidBodySim,self).checkConfig(interact);         
       self.__checkConfig()
       
    def __convertValues(self):
        self.cRigidBody = self.configDict["RigidBodySim"]   
    
    def __checkConfig(self):
        
        if not os.path.exists(self.cRigidBody.sceneFileTemplate) and not os.path.lexists(self.cRigidBody.sceneFileTemplate):
            raise CE.MyValueError("Scenefile %s does not exist!" % self.cRigidBody.sceneFileTemplate)
    
    def printOptions(self):
        super(RigidBodySim,self).printOptions();
        #CE.printKeyMessage("Scenefile","%s" % self.cRigidBody.sceneFile)
        
    def generate(self):

        
        # Parent config dict is none
        configDicts = [None]        
        
        if self.cCluster.jobIdxParent >= self.cCluster.nJobs-1:
            raise CE.MyValueError("jobIdxParent=%i not feasible, since you generate %i jobs from idx 0 till %i !" % (self.cCluster.jobIdxParent,self.cCluster.nJobs, self.cCluster.nJobs-1) )
        for jobIdx in range(0,self.cCluster.nJobs):
            
            CE.printHeader("Generating MPI Job: RigidBody Simulation =================")
            CE.printKeyMessage("JobIndex","%i" % jobIdx + (" (not files because parent job!)" if jobIdx <= self.cCluster.jobIdxParent else "") )
            
             # first make a new self.config
            self.config = self.makeInterpolationConfig();
            
            # setting the jobIdx
            self.config["Job"]["jobIdx"] = str(jobIdx)
            
            self.config["Job"]["submitCommand"] = " ".join([self.config["Cluster"]["submitCommand"] , 
                        (configDicts[-1].Cluster.submitArgsChainJob if jobIdx > self.cCluster.jobIdxParent+1 else "") , self.config["Job"]["submitArgs"]])            
            
            
            # final interpolation of all automatic generated options and conversion to self.configDict
            # and checking of feasible values before template writting
            # from now self.cCluster , self.cJob and self.cRigidBodySim are available (reference to self.configDict)
            self.convertValues()
            
            
            
            # only generate files for the job for jobIndices which are greater then jobIdxParent
            # jobIdxParent is the parent job, which we base our nJobs on 
            if jobIdx > self.cCluster.jobIdxParent :            
                
                self.checkConfig(interact=self.cCluster.interact)
                self.printOptions()

                # make job script dir (if exists, try to remove it, if no -> abort)
                cF.makeDirectory( self.cJob.scriptDir, name="Job script dir", defaultMakeEmpty=False, interact= self.cCluster.interact)
                self.writeJobScriptArgs( os.path.join(self.cJob.scriptDir, "configureScriptArgs.txt" ) )
                
                
                # write all templates
                self.writeTemplates(self, configDicts);
               
                # check if we submit the job
                if self.cCluster.submitJobs:
                    print("Trying to submit job with command: \n%s" % self.cJob.submitCommand)
                    cF.callProcess(self.cJob.submitCommand)
                    
            #end if
            
            # save conficDict for next jobIdx (possibly)
            configDicts.append(self.configDict)
            
            CE.printHeader("==========================================================")
        
        # Write total submit file to first folder 
        config0 = configDicts[self.cCluster.jobIdxParent+2];
        filePath = os.path.join(config0.Job.scriptDir,"submitAll.sh")
        f = open(filePath,"w+")
        commands = [];        
        for c in configDicts[self.cCluster.jobIdxParent+2:]:
            if c:
                commands.append(c.Job.submitCommand)
        
        f.write("\n".join(commands))     
        cF.makeExecutable(filePath);        
