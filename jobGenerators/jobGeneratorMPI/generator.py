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


from JobGenerator.jobGenerators.generator import Generator
from JobGenerator.jobGenerators.importHelpers import ImportHelpers as iH
from JobGenerator.jobGenerators.commonFunctions import CommonFunctions as cf


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
        self.config["Job"]["localDir"]  = os.path.abspath(cf.expandEnvVar(self.config["Job"]["localDir"],self.envRegexPattern))
        self.config["Job"]["globalDir"] = os.path.abspath(cf.expandEnvVar(self.config["Job"]["globalDir"],self.envRegexPattern))
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
            raise ValueError("Start Script template %s does not exist!" % self.cTemplates.startJob)        
        if not path.exists(self.cTemplates.preProcessPerNode):
            raise ValueError("Start Script template %s does not exist!" % self.cTemplates.preProcessPerNode)        
        if not path.exists(self.cTemplates.processPerCore):
            raise ValueError("Start Script template %s does not exist!" % self.cTemplates.processPerCore)        
        if not path.exists(self.cTemplates.postProcessPerNode):
            raise ValueError("Start Script template %s does not exist!" % self.cTemplates.postProcessPerNode)        
        if not path.exists(self.cTemplates.endJob):
            raise ValueError("Start Script template %s does not exist!" % self.cTemplates.endJob)        
            
        if self.cJob.copyLocation and not path.exists(self.cJob.copyLocation):
            raise ValueError("Copy location %s does not exist!" % self.cJob.copyLocation)       
        
        cf.checkNotExisting(self.cJob.globalDir,interact=interact,name="Global dir")
        
        # add no tar command if not tarCommandToGlobalDir is not specified
        if "tarCommandToGlobalDir" not in self.cJob:
            self.cJob["tarCommandToGlobalDir"] = ""
        
        
        if "pathChecker" in self.cJob:
            pathChecker = cf.jsonParse(self.cJob.pathChecker)
            pathChecker = cf.flatten(pathChecker)
            for s in pathChecker:
                if not os.path.exists(s) or not os.path.lexists(s):
                     raise ValueError("file: %s does not exist!" % s)
            
        # check executbles with which and return correct path
        if "executableChecker" in self.cJob:
            execCheck = cf.jsonParse(self.cJob.executableChecker)
            for varAccess,ex in execCheck:
                exec("self.configDict"+varAccess +"= cf.checkExecutable(ex)")
        
        
    def generate(self):
        pass
    
        
    def printOptions(self):
        super(GeneratorMPI,self).printOptions()
        print( "-> Local Dir: %s" % self.cJob.localDir )
        print( "-> Global Dir: %s" % self.cJob.globalDir )
        print("-> Executable command: %s" % self.cJob.executableCommand)
        

