import math
from string import Template

import HPCJobConfigurator
from HPCJobConfigurator.jobGenerators.dictionaryAdjuster import DictionaryAdjuster 


class SubmitFileGenerator():
  
    def __init__(self,jobGenModules):
        self.cF = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
    
    
    def __call__(self, generator, inputFile, outputFile, configDict, lastConfigDicts, *largs, **kwargs):
        
        
        # Example per Job: We define two boring parameters depending on the jobId
        file = open( outputFile, "w")
        
        for jobNr in range( int(configDict["Settings"]["startIdx"]), 
                            int(configDict["Settings"]["endIdx"]) ):
            
            command = Template( configDict["Settings"].submitFormatString ).substitute( {"jobNr":jobNr} ) 
            file.write( command +"\n" )
            
        
        file.close()
        
            
            
            
            
       
        
        