#!/usr/bin/env python

# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import sys,os
import os.path as path
import argparse
import colorama


if sys.version_info[0] != 3:
    print("This script is only python3 compatible!")
    exit(1)
    
try:
    import configargparse as cap
    from attrdict import AttrMap
except ImportError as e:
       raise NameError("You don't have module %s installed. Please install or put the in the external directory" % e.name)


import inspect, os

# set the directory of the module
configuratorModuleDir = os.path.abspath(os.path.join(os.path.dirname(
                                    inspect.getfile(inspect.currentframe())
                                    )
                                  ))
                                  
#  set the module path for this module
configuratorModulePath = os.path.abspath(os.path.join(configuratorModuleDir,".."))

# set the path such that the configurator module gets found
sys.path.append( configuratorModulePath )

import HPCJobConfigurator.jobGenerators as jg
from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF
from HPCJobConfigurator.jobGenerators import configuratorExceptions as CE

def configJob(configFile="Launch.ini", overwriteArgs = None, colorOutput=False):
    
    if colorOutput:
      # initialize terminal colors
      CE.doColoredOutput()
    
    p =  cap.ArgParser( default_config_files=[configFile])
    p.optionxform = str # dont make names lower case!
    
    # str = lambda s: s.lstrip('"').rstrip('"')
    
    p.add('-c', '--config', required=False, is_config_file=True, help='The configuration file path.')
    p.add( "-f", '--submitJobs', default="False", type=str, help=
            """Submitting the job at the end of the process generation, by using the jobs launch commmand
               which is set in the options ${Cluster:jobGeneratorConfig} or with the command -x             
            """)
    p.add( "-l","--localScratchPerCore", type= str, required=True ,
          help="""This is the local scratch size per core on the cluster.""" )  
    p.add( "-r","--ramPerCore", type=str, required=True,
          help="""This is the amount of memory each core should have on the cluster.""")                          
    p.add( "-t","--runTime", type=str, required=True,
          help="""This specifies the amount of time this job can run until it is killed.""" )                      
    p.add( "-p","--nProcesses", type=str, default="1" ,
          help="""The number of cores or processes to use on the cluster.""")                          
    p.add( "-n","--nJobs", type=str,  default="1",
          help="""The number of jobs to generate succesively by the generator for this job name. Jobs with indices [0,nJobs+1] are configured!""")
          
    p.add( "--jobIdxParent", type=str,  default="-1",
          help="""The parent job idx, if specified only job files for jobs with indices in [jobParentIdx+1,nJobs-1] 
                  are generated (other jobs are left untouched).""")

    p.add( "--jobGeneratorOutputDir", type=str,  default="./",
          help="""The generators output directory, where all scripts and other stuff is written to,
          to successfully launch the job.""")   
    p.add( "-j","--jobName", type=str, required=True,
          help="The job's name on the cluster.")  
    p.add( "-g","--jobGenerator", type=str, required=True,
          help="""This is the python class which sets the generator to use to generate the jobs. 
                  This is a namespace string as used in import statements in python, 
                  how ever the last string after the last dot denotes the class type.""")
    p.add( "-x","--jobGeneratorConfig", type=str, required=True,
          help="""The job generator configuration file (.ini) which is used by the job generator.""" )

    p.add( "-m","--mailAddress", type=str, default="",
          help="""The email address to use""")
    p.add( "-s", "--submitCommand", type=str, default="", required=True ,
          help="""The submit command which is used on the cluster to submit one job (e.g bsub) """)
    p.add( "--submitArgsChainJob", type=str, default="",
          help="""If the jobs should be chained together, that means each job is dependent on the last 
               one you should enter here the additional arguments to ${Cluster:submitCommand} to make that happen.
               This argument is fully evaluated and appended to the next jobs ${Cluster:submitCommand} !""")  
    p.add( "-v","--verbose", type=str, default="False",
          help="""Shows additional information, (depending on the generator), usage: --verbose=True """)
    
    p.add( "-i","--interact", type=str, default="True",
          help="""Interact with the user. If True, the script may interact when certain errors appear. Such as removing directories and so on. usage: --interact=False """) 
   
    args = p.parse_args()
    print(p.format_values()) 
    
    dic = vars(args);
    if overwriteArgs is not None:
        dic.update(overwriteArgs)
    
    
    configJobInternal(dic)  
    
    if colorOutput:
      CE.undoColoredOutput() 

def configJobInternal(config):
    
    # Get cluster config values
    # Cluster section is ignored, add it again
    d = AttrMap( config )
    
    # remove "config" value and convert boolean flags to strings again, 
    # these config is used only with strings in the generator
    d.pop("config")    
    config = AttrMap( { "Cluster" : d } )

    # add the modules path of this file, which can be used in the (.ini files)
    # and also the execDir of the submit.py
    config["General"] = {
                         "configuratorModuleDir" : configuratorModuleDir,
                         "configuratorModulePath" : configuratorModulePath,
                         "currentWorkDir" : os.getcwd(),
                         "jobDir" : os.path.dirname(os.path.abspath(config.Cluster.jobGeneratorConfig)),
                         "configureScriptArgs" : " ".join(sys.argv)
                         }
                         
    config.Cluster.jobGeneratorOutputDir = os.path.abspath(config.Cluster.jobGeneratorOutputDir )
    
    
    
    # load generator module dyanamically and start the job generator
    # load the given Cluster.jobGenerator class
    module, generatorClass = iH.importClassFromModuleString(config.Cluster.jobGenerator, verbose=True)
    
    gen = generatorClass(config)
    gen.generate()
    
    return 0


if __name__ == "__main__":
   err=configJob(colorOutput=True)
   sys.exit(err);
