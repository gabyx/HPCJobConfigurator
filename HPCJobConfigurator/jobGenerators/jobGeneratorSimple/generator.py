# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os


from HPCJobConfigurator.jobGenerators.importHelpers import ImportHelpers as iH
from HPCJobConfigurator.jobGenerators.commonFunctions import CommonFunctions as cf
from HPCJobConfigurator.jobGenerators.generator import Generator



class GeneratorSimple(Generator):
    
    def __init__(self,clusterOptions):
        super(GeneratorSimple,self).__init__(clusterOptions );

    def convertValues(self):
       super(GeneratorSimple,self).convertValues();         
       self.__convertValues()
    
    def checkConfig(self,interact = True):
       super(GeneratorSimple,self).checkConfig(interact);         
       self.__checkConfig()
       
    def __convertValues(self):
        pass
    
    def __checkConfig(self):
        pass
    
    def printOptions(self):
        super(GeneratorSimple,self).printOptions();
        
    def generate(self):

        # Parent config dict is none
        configDicts = [None]        
        
        if self.cCluster.jobIdxParent >= self.cCluster.nJobs-1:
            raise ValueError("jobIdxParent=%i not feasible, since you generate %i jobs from idx 0 till %i !" % (self.cCluster.jobIdxParent,self.cCluster.nJobs, self.cCluster.nJobs-1) )
        for jobIdx in range(0,self.cCluster.nJobs):
            
            print("Generating Simple Job: ====================================")
            print("-> JobIndex: %i" % jobIdx + (" (not files because parent job!)" if jobIdx <= self.cCluster.jobIdxParent else "") )
            
            # first make a new self.config
            self.config = self.makeInterpolationConfig();
            
            # setting the jobIdx
            self.config["Job"]["jobIdx"] = str(jobIdx)
            
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
                cf.makeDirectory( self.cJob.scriptDir, name="Job script dir", defaultMakeEmpty=False, interact= self.cCluster.interact)
                self.writeJobScriptArgs( os.path.join(self.cJob.scriptDir, "submitScriptArgs.txt" ) )
                
                
                # write all templates
                self.writeTemplates(self, configDicts);
                                    
            # save conficDict for next jobIdx (possibly)
            configDicts.append(self.configDict)
            
            print("==========================================================")
        