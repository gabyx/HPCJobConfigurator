# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os,re,sys,copy
import os.path as path

from attrdict import AttrMap
import configparser
from configparser import ConfigParser, ExtendedInterpolation

from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF
from HPCJobConfigurator.jobGenerators.dictionaryAdjuster import DictionaryAdjuster
from HPCJobConfigurator.jobGenerators import configuratorExceptions as CE

class MyConfigParser(ConfigParser):
    
    def __init__(self,defaults,optionxform=str,*args,**kargs):
        super(MyConfigParser,self).__init__(*args,**kargs)
        self.optionxform = optionxform;
        for sec, options in defaults.items():
            self.add_section(sec)
            for opt,value in options.items():
                #print(opt,type(opt),type(value))
                super(MyConfigParser,self).set(sec,opt,value)


class MyExtendedInterpolation(ExtendedInterpolation):
    """ ExtendedInterpolation which has a dictionary 
        of key= sections , values = set of options for this section
        e.g. self.nonInterpolatedOpts = { "sec1": set(["opt1","opt2","opt3"]), "sec2" : set(["opt1"]) } 
        which denote namespaced (section) options which are skipped when interpolating 
        if the skipping is enabled (see enableSkipping function, default is True)
        Skipped values always have a section and are in the form '${section:options}' or '$section:option'
        Extensions to ExtendedInterpolation in this implementation are marked with 'Extension here:'
    """
    def __init__(self,nonInterpolatedOpts={}, enableSkipping = True):
        self.nonInterpolatedOpts = nonInterpolatedOpts
        self.skipping = enableSkipping
#        
    def setSkipping(self,f):
        self.skipping = bool(f)            
    
    def before_get(self, parser, section, option, value, defaults):
        L = []
        self._interpolate_some(parser, option, L, value, section, defaults, 1)
        return ''.join(L)

    def before_set(self, parser, section, option, value):
        tmp_value = value.replace('$$', '') # escaped dollar signs
        tmp_value = self._KEYCRE.sub('', tmp_value) # valid syntax
        if '$' in tmp_value:
            raise ValueError("invalid interpolation syntax in %r at "
                             "position %d" % (value, tmp_value.find('$')))
        return value

    def _interpolate_some(self, parser, option, accum, rest, section, map,
                          depth):
        if depth > configparser.MAX_INTERPOLATION_DEPTH:
            raise InterpolationDepthError(option, section, rest)
        while rest:
            p = rest.find("$")
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]
            if c == "$":
                accum.append("$")
                rest = rest[2:]
            elif c == "{":
                m = self._KEYCRE.match(rest)
                if m is None:
                    raise configparser.InterpolationSyntaxError(option, section,
                        "bad interpolation variable reference %r" % rest)
                path = m.group(1).split(':')
                rest = rest[m.end():]
                sect = section
                opt = option
                
                # Extension here:
                recursive = True # this gets set to False if the path is in elf.nonInterpolatedOpts
                
                try:
                    
                    if len(path) == 1:
                        # interpolate the value e.g: " some value and ${opt}) "
                        opt = parser.optionxform(path[0])
                        v = map[opt]
                    elif len(path) == 2:
                        # interpolate the value e.g: " some value and ${sect:opt}) "
                        sect = path[0]
                        opt = parser.optionxform(path[1])
                        
                        # Extension here:
                        #skip values which are in the dict
                        
                        if self.skipping  and sect in self.nonInterpolatedOpts and opt in self.nonInterpolatedOpts[sect]:
                                v = "${%s}" % m.group(1)
                                recursive = False;
                        else:
                            v = parser.get(sect, opt, raw=True)
                    else:
                        raise configparser.InterpolationSyntaxError(
                            option, section,
                            "More than one ':' found: %r" % (rest,))
                            
                except (KeyError, configparser.NoSectionError, configparser.NoOptionError):
                    raise configparser.InterpolationMissingOptionError(
                        option, section, rest, ":".join(path))
                        
                if "$" in v and recursive:
                    self._interpolate_some(parser, opt, accum, v, sect,
                                           dict(parser.items(sect, raw=True)),
                                           depth + 1)
                else:
                    accum.append(v)
            else:
                raise configparser.InterpolationSyntaxError(
                    option, section,
                    "'$' must be followed by '$' or '{', "
                    "found: %r" % (rest,))
                   
# Generator for simluation jobs on the cluster

class Generator:
    nonInterpolatedOptions = {}
    
#    essentialOptions = {
#    "Cluster":
#        {
#            "jobName",
#            "runTime",
#            "ramPerCore",
#            "runTime",
#            "ramPerCore",
#            "localScratchPerCore",
#            "nProcesses",
#            "nJobs",
#            "jobGeneratorOutputDir",
#            "jobGenerator",
#            "jobGeneratorConfig",
#            "submitCommand",
#            "submitArgsChainJob",
#            "submitJobs",
#            "mailAddress",
#            "verbose"
#        }
#    "Job": 
#        {
#            "submitCommand"
#        }
#    "Templates":
#        {
#             "submitJob"
#        }
#    }    
                                
    envRegexPattern = "ENV::(\w*)"    
    
    def __init__(self,config, nonInterpolatedOpts = {}):
        
        # functor classes which configure certain templates
        self.templateConfigurators = {}
        
        self.nonInterpolatedOpts = Generator.nonInterpolatedOptions.copy()
        self.updateNonInterpolatedOpts(self.nonInterpolatedOpts, nonInterpolatedOpts) 

        # save the arguments, which have been passed to the submit.py script!
        self.configureScriptArgs = config["General"]["configureScriptArgs"]
        
         # temporary copy (no interpolation anymore in this configs))
        self.cCluster   = copy.deepcopy(config["Cluster"])
        self.__convertClusterConfig()
        
        # first parse the job configuration file in self.cCluster.generatorConfig file (${Cluster:generatorConfig}) 
        # MyConfigParser is there to inject config into the ConfigParser to succesfully interpolate the values 

        p = MyConfigParser(defaults = config, interpolation = None, strict = True)
        if not os.path.exists(self.cCluster.jobGeneratorConfig):
            raise ValueError("Config file %s does not exist!" % self.cCluster.jobGeneratorConfig)
        p.read(self.cCluster.jobGeneratorConfig)
        # original non interpolated  config
        self.configDictOrig = self.convertConfig(p)
        
        # make self.config which is interpolated
        self.interpolation = MyExtendedInterpolation(self.nonInterpolatedOpts)   
        self.config = self.makeInterpolationConfig()
        
        # This self.config can be changed and modified, 
        # and is then converted to self.configDict (everything interpolated) in __convertValues
        # a generator subclass should always call makeInterpolationConfig() which reinitializes the interpolation config
        self.configDict = None
        
        # make default dictionary adjuster for default template specifiations
        d = DictionaryAdjuster({"commonFunctions":cF,"importHelpers":iH})
        self.templateConfigurators[self.makeConfiguratorHash("dictionaryAdjuster","DictionaryAdjuster")] = d
        self.defaultTemplateConfigurator = d
        
    def makeInterpolationConfig(self):
        return MyConfigParser(defaults = self.configDictOrig, interpolation = self.interpolation , strict = True)
        
    def convertValues(self):

        # check for each template options if there is an option already in TemplatesOut with the same name
        # set the output path for this template to the default otherwise
        if "TemplatesOut" not in self.config:
            self.config["TemplatesOut"] = {}

        # set for each template the TemplatesOut path, if not defined yet, (default is job script dir)
        if "Templates" in self.config:
            for k,templ in self.config["Templates"].items():
                if k not in self.config["TemplatesOut"]:
                    
                    if not os.path.exists(templ): # this is no valid file
                        raise ValueError("You did not specify an output file for option %s in section TemplatesOut! and template: %s is no existing file!" % (k,templ))
                        
                    self.config["TemplatesOut"][k] = os.path.join( self.config["Job"]["scriptDir"], os.path.basename(templ) )
        else:
            print("Generator:: WARNING: No [Template] section defined -> no templates to configure")

        self.__convertValues()
        
        # make easy accesible references
        self.cJob= self.configDict["Job"]
        self.cTemplates = self.configDict["Templates"]
        self.cTemplatesOut = self.configDict["TemplatesOut"]
        
    def checkConfig(self, interact = True):
        self.__checkConfig(interact)
        
    def generate(self):
        self.printOptions()
    
    def __convertValues(self):
        if not self.config:
            raise ValueError("self.config has not been set in generator subclass")
        # make nice dict and remove all quotes
        # switch all interpolation on and interpolate all values
        # this conversion is done for each job!
    
        self.interpolation.setSkipping(False)
        self.configDict = self.convertConfig(self.config)
        # expand all env vars
        for sec,dic in self.configDict.items():
            self.configDict[sec] = self.expandEnvVars(dic)
            
        #self.cCluster = self.configDict["Cluster"]  
        ## get reference again from config (might have changed values depending on subclass)
        #self.__convertClusterConfig()
    
    def __convertClusterConfig(self):
        
        # convert some values
        self.cCluster.runTime = int(self.cCluster.runTime)
        self.cCluster.ramPerCore = int(self.cCluster.ramPerCore)
        self.cCluster.localScratchPerCore = int(self.cCluster.localScratchPerCore)
        self.cCluster.nProcesses = int(self.cCluster.nProcesses)
        self.cCluster.nJobs = int(self.cCluster.nJobs)
        self.cCluster.jobIdxParent = int(self.cCluster.jobIdxParent)
        self.cCluster.verbose = cF.toBool(self.cCluster.verbose,"verbose")
        self.cCluster.interact = cF.toBool(self.cCluster.interact,"interact")
        self.cCluster.submitJobs = cF.toBool(self.cCluster.submitJobs,"submitJobs")
        
        
        
    def printOptions(self):
        CE.printKeyMessage("Submit command:",self.cCluster.submitCommand )
        CE.printKeyMessage("Submit args chain jobs","%s" % self.cCluster.submitArgsChainJob )
        CE.printKeyMessage("Run time","%i min " % self.cCluster.runTime)
        CE.printKeyMessage("Ram/Core size","%i mb" % self.cCluster.ramPerCore)
        CE.printKeyMessage("Scratch/Core size","%i mb" % self.cCluster.localScratchPerCore)
        CE.printKeyMessage("Number of processes","%i" % self.cCluster.nProcesses )
        CE.printKeyMessage("Job output dir","%s" % self.cCluster.jobGeneratorOutputDir)
        
    def convertConfig(self,config):
        """Converts a ConfigParser config to a AttrDict"""
        return AttrMap({s: AttrMap({k:copy.copy(v) for k,v in config.items(s)}) for s in config.sections()})
    
    
    def __checkConfig(self, interact):
        # Check all values


        cF.makeDirectory(self.cCluster.jobGeneratorOutputDir, interact=False, name="Job output dir")
        self.cCluster.jobGeneratorOutputDir = os.path.abspath(self.cCluster.jobGeneratorOutputDir);
            
        if not path.exists(self.cCluster.jobGeneratorConfig):
            raise NameError("Job config file: %s does not exist!" % self.cCluster.jobGeneratorConfig)
        else:
            self.cCluster.jobGeneratorConfig = os.path.abspath(self.cCluster.jobGeneratorConfig);

            
        if(self.cCluster.nProcesses < 1):
            raise NameError("Process number: %i wrong (>1)!" %  self.cCluster.nProcesses )
        if(self.cCluster.runTime < 0):
            raise NameError("Run time value: %i wrong (>1)!" %  self.cCluster.runTime )
        if(self.cCluster.ramPerCore < 1):
            raise NameError("Ram per core value: %i wrong (>1)!" % self. cCluster.ramPerCore )
        if(self.cCluster.localScratchPerCore < 1):
            raise NameError("Local scratch per core value: %i wrong (>1)!" %  self.cCluster.localScratchPerCore )
            
        if(self.cCluster.nJobs < 1):
            raise NameError("Number of jobs to generate: %i wrong (>1)!" %  self.cCluster.nJobs )
        
    
    def expandEnvVars(self,dic):
        """Expands all environment variables in the dictionary dic"""
        for key,value in dic.items():
            dic[key] = cF.expandEnvVar(value,self.envRegexPattern);
        return dic
    
    def updateNonInterpolatedOpts(self,nonInpOpts, nonInterpolatedOpts):
        for sec,opts in  nonInterpolatedOpts.items():
            if sec in nonInpOpts:
                nonInpOpts[sec].update(opts)
            else:
                nonInpOpts[sec] = opts
    
    
    def writeTemplates(self , generator, configDicts ):

        # iterate over all template strings
        for k,templ in self.cTemplates.items():
            
            # get output file
            outFile = self.cTemplatesOut[k]
            
            # interprete the string as a json string if the first character is a {
            # { "inputFile" : "?" , "outputFile": "??" , "configurator" : "??" }
            # otherwise it is intrepreted as a inputFile which is configurated with the standart 
            # configurator which replaces strings and the output goes into the Job:scriptDir
            # where the file is made executable
            templ = templ.strip()
            
            configurator = None
            
            if templ and templ[0] == "{":
                templ = cF.jsonParse(templ)
                
                settings = {}
                if "settings" in templ:
                    settings = templ["settings"]
                
                inFile = templ["inputFile"]
                configurator = templ["configurator"] # jobConfigurator.generatorRigidBody.adjuster or what ever
                # only load each configurator once
                configuratorHash = self.makeConfiguratorHash(**configurator)
                
                 # load the special configurator if not loaded yet
                if configuratorHash not in self.templateConfigurators:
                    
                    if self.cCluster.verbose:
                        print("Generator:: Running template configurator: " , configurator )
                        print(" \tinputFile: %s\n" % inFile if inFile else "" + "\toutputFile: %s" % outFile)
                    
                    moduleType, classType = iH.importClassFromModule(**configurator)
                    self.templateConfigurators[configuratorHash] = classType({"commonFunctions":cF,"importHelpers":iH}) # make instance (hand over modules)

                configuratorFunc = self.templateConfigurators[configuratorHash];
                
                # configure file
                configuratorFunc(generator, inFile, outFile, self.configDict, configDicts, verbose=self.cCluster.verbose, **settings )
                
            else:
                # use standart dictionary adjuster as default
                inFile = templ
                #configure file
                self.defaultTemplateConfigurator(generator,inFile, outFile, self.configDict, configDicts, verbose=self.cCluster.verbose, makeExecutable=True)
               
                
    def makeConfiguratorHash(self,modulePath,className,**kwargs):
      return hash(modulePath + className)
      
    def writeJobScriptArgs(self,file):
        f = open(file,"w")
        f.write(self.configureScriptArgs)
  