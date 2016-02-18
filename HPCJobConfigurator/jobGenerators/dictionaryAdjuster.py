# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

from string import Template
import pprint


''' The template pattern '''
templatePattern       = r'''(?P<escaped>\$\$) # Escape sequence of two delimiters
                        |
                        (?:\$\{(?P<braced>[_a-zA-Z-][_a-zA-Z0-9-]*(?::[_a-zA-Z0-9-][_a-zA-Z0-9-]*)+)\}) # delimiter and a braced identifier, e.g. ${Section:idx}
                        |
                        (?:\$(?P<named>[_a-zA-Z-][_a-zA-Z0-9-]*(?::[_a-zA-Z0-9-][_a-zA-Z0-9-]*)+))      # delimiter and a non-braced identifier,  e.g. $Section:idx
#                            |
#                            \$(?P<invalid>)                                      # Other ill-formed delimiter exprs
                        '''
# for example : ${experiment:5:aabbPixelCoordinates:minPoint} is allowed but not ${4H:5:aabbPixelCoordinates:minPoint}
# we allow subsequent names between : ... :  to start with a number, except the first one! 


class DictionaryAdjuster:
    

    class MyTemplate(Template): pattern = templatePattern
       
    
    # General recursive formatter
    def stringFormatter(self,v):
      if isinstance(v,list):
        print("LIST::::" , v)
        s=""
        for i in v[:-1]:
            s+=self.stringFormatter(i)+" "
        s+=self.stringFormatter(v[-1])
        return s
      elif isinstance(v,bool):
        return "true" if v else "false"
      else:
        return str(v)
        
    
    def __init__(self,jobGenModules):
        self.cF = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
        
        self.currentConfigDictId = None
        
        self.prettyPrint = pprint.PrettyPrinter(indent=2)
    
    def __call__(self, generator, inputFile, outputFile,
                 configDict, lastConfigDicts, verbose = True , makeExecutable = False, additionalFiles=[], makeReplacementOnceForId = True):
        
        """ 
            Template configurator:
            This is a simple adjuster which loads a json file into a dictionary
            makes a flattened dictionary out of it, e.g. {"AA:a:d" : 3} 
            and adjusts all references in the template with this replacement dictionary,
            e.g ${AA:a:d} ->  "3"
            makeReplacementOnceForId=True only converts for each  typeid(conficDict) once!
        """

        for fileSpec in additionalFiles:
          
          if not isinstance(fileSpec,dict):
            raise ValueError("fileSpecification in 'additionalFiles' is not a list of dictionaries") 
          
          if "parentName" in fileSpec:
            parentName=fileSpec["parentName"]
            if parentName in configDict:
              raise NameError("This parent name: %s,  for additional configDict %s does already exist!",(parentName,fileSpec))
          else:
            parentName = None

          # load file as json and  add it under the key: parentName if defined
          try:
            d = self.cF.jsonLoad(fileSpec["path"])
          except Exception as e:
            print("Error in json parsing of file %s" % fileSpec["path"])
            raise e  
        
          if parentName is not None:
            dic = { parentName :  d}
          else:
            dic = d
            
          # and update configDict
          configDict.update(dic)
        
        # make replacement dict and write template
        convert = False
        if makeReplacementOnceForId:
          if id(configDict) != self.currentConfigDictId:
           self.currentConfigDictId = id(configDict)
           convert = True
        else:
          convert = True   
          
        if convert:
          self.replacementDict = self.cF.flattenDict(configDict,formatter=self.stringFormatter)
        
        if(verbose):
           print("Replacement dictionary for file %s:" % inputFile)
           self.prettyPrint.pprint(self.replacementDict)

        self.inputFile = inputFile # save in class for log output if error
        self.writeTemplate(inputFile,self.replacementDict,outputFile,makeExecutable)
    
    
    def writeTemplateStr(self,string, substDict, outputFile):
        src = self.MyTemplate( string )
        try:        
            t = src.substitute( substDict )
        except KeyError as k:
            raise ValueError("Template substitution from input file: '%s' \nto output file '%s' failed for substitution %s" % (self.inputFile,outputFile,k) )
        fileout = open( outputFile, 'w+')
        fileout.write(t)      
    
    def writeTemplate(self,templateFile, substDict, outputFile, makeExecutable=False):
        """ Write a template file at directory outputDir with substitution dictionary substDict
            and return the filePath string   
            outputPath can be the same as the input templateFile, which overwritesa the file with the substitute values
        """ 
        #open the file
        filein = open( templateFile ,'r')
        self.writeTemplateStr(filein.read(),substDict , outputFile)
        
        if makeExecutable :
          self.cF.makeExecutable( outputFile )
        
