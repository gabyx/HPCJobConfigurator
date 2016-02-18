# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================



import os
import os.path as path
import re
import ast
from attrdict import AttrDict, AttrMap
from configparser import ConfigParser, ExtendedInterpolation


from HPCJobConfigurator.jobGenerators.generator import Generator
from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF
from HPCJobConfigurator.jobGenerators import configuratorExceptions as CE

class GeneratorMPI(Generator):
    
    # automatic generated options which are not interpolated till the end
    nonInterpolatedOptions = {"Job" : set() }
    
    
    # make essential options list, which need to be specified
#    essentialOptions = {
#    "Job": 
#        {
#             "localDir",
#             "globalDir", 
#             "scriptDir", 
#             "copyLocation", 
#             "executableCommand"
#        }
#    "Templates":
#        {
#             "launch",
#             "startJob",
#             "preProcessPerNode",
#             "processPerCore",
#             "postProcessPerNode",
#             "endJob"
#        }
#    }
    
    
    def __init__(self,clusterOptions, nonInterpolatedOpts = {}):
        
        # merge input non interpolated options with internal
        nonInpOpts = GeneratorMPI.nonInterpolatedOptions.copy()
        self.updateNonInterpolatedOpts(nonInpOpts, nonInterpolatedOpts)        

        super(GeneratorMPI,self).__init__(clusterOptions,nonInpOpts);
        
        
        self.cJob= None
        self.cTemplates = None
        
    def convertValues(self):
        
        # Before any interpolation and conversion, convert essential 
        # local and global dir to absolut paths!
        # important, because its more safe!
        self.interpolation.setSkipping(False)  # turn interpolation on
        
        self.config["Job"]["localDir"]  = cF.expandEnvVar(self.config["Job"]["localDir"],self.envRegexPattern, errorIfNotFullyExpanded=False)
        # allow Job:localDir to contain '$VAR' variables, are expanded by shell
        if "$" in self.config["Job"]["localDir"]:
            CE.printWarning("Your Job:localDir: %s contains '$' character, which are only expanded in Bash!" % self.config["Job"]["localDir"])
        
        self.config["Job"]["globalDir"] = os.path.abspath(cF.expandEnvVar(self.config["Job"]["globalDir"],self.envRegexPattern, errorIfNotFullyExpanded=True))
        # Job:globalDir is made absolute to execution dir when configuring
        
        # convert and interpolate all values in base class
        super(GeneratorMPI,self).convertValues();         
        
        # do some other conversion for this generator values
        self.__convertValues()
       
    def checkConfig(self, interact):
       super(GeneratorMPI,self).checkConfig(interact);         
       self.__checkConfig(interact)
        
    def __convertValues(self):
        pass
        
    def __checkConfig(self,interact):
        
        
        # expand global and local dirs
        
        if not path.exists(self.cTemplates.startJob):
            raise CE.MyValueError("Start Script template %s does not exist!" % self.cTemplates.startJob)        
        if not path.exists(self.cTemplates.preProcessPerNode):
            raise CE.MyValueError("Start Script template %s does not exist!" % self.cTemplates.preProcessPerNode)        
        if not path.exists(self.cTemplates.processPerCore):
            raise CE.MyValueError("Start Script template %s does not exist!" % self.cTemplates.processPerCore)        
        if not path.exists(self.cTemplates.postProcessPerNode):
            raise CE.MyValueError("Start Script template %s does not exist!" % self.cTemplates.postProcessPerNode)        
        if not path.exists(self.cTemplates.endJob):
            raise CE.MyValueError("Start Script template %s does not exist!" % self.cTemplates.endJob)        
            
        if self.cJob.copyLocation and not path.exists(self.cJob.copyLocation):
            raise CE.MyValueError("Copy location %s does not exist!" % self.cJob.copyLocation)       
        
        cF.checkNotExisting(self.cJob.globalDir,interact=interact,name="Global dir")
        
        # add no tar command if not tarCommandToGlobalDir is not specified
        if "tarCommandToGlobalDir" not in self.cJob:
            self.cJob["tarCommandToGlobalDir"] = ""
        
        
        if "pathChecker" in self.cJob:
            pathChecker = cF.jsonParse(self.cJob.pathChecker)
            pathChecker = cF.flatten(pathChecker)
            for s in pathChecker:
                if not os.path.exists(s) or not os.path.lexists(s):
                     raise CE.MyValueError("file: %s does not exist!" % s)
            
        # check executbles with which and return correct path
        if "executableChecker" in self.cJob:
            execCheck = cF.jsonParse(self.cJob.executableChecker)
            for varAccess,ex in execCheck:
                exec("self.configDict"+varAccess +"= cF.checkExecutable(ex)")
        
        
    def generate(self):
        pass
    
        
    def printOptions(self):
        super(GeneratorMPI,self).printOptions()
        print( "-> Local Dir: %s" % self.cJob.localDir )
        print( "-> Global Dir: %s" % self.cJob.globalDir )
        print("-> Executable command: %s" % self.cJob.executableCommand)
        

