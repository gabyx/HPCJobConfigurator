import math

import HPCJobConfigurator
from HPCJobConfigurator.jobGenerators.dictionaryAdjuster import DictionaryAdjuster 


class SimpleConfigAdjuster(DictionaryAdjuster):
  
    def __init__(self,jobGenModules):
        super(SimpleConfigAdjuster,self).__init__(jobGenModules)
    
    
    def __call__(self, generator, inputFile, outputFile, configDict, lastConfigDicts, *largs, **kwargs):
        # we forward all arguments to the DictionaryAdjuster
        
        # Here we can customize the adjustement of the inputFile
        # per JobId
        
        
        
        # Example per Job: We define two boring parameters depending on the jobId
        print("SimpleConfigAdjuster::  configuring file: %s" % outputFile)
        jobIdx = int(configDict["Job"]["jobIdx"])
        
        configDict["Settings"]["parameter1"] = str( math.sin( jobIdx / 10 ) )
        configDict["Settings"]["parameter2"] = str( math.cos( jobIdx / 10 ) )
        
        
        # Now we adjust the input file by calling the DictionaryAdjuster
        
        super(SimpleConfigAdjuster,self).__call__(generator, inputFile, outputFile, configDict, lastConfigDicts, *largs, **kwargs)
        
        
        
        # Example per Process: 
        # We can here of course also generate a config file for each process. 
        #       use configDict["Cluster"].nProcesses and place the file in configDict["Job"].jobDir
        # such that each config file would describe which part the task in process.sh will work on
        
        