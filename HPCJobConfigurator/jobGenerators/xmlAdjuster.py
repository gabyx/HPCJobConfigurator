# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import shutil
import os
import os.path as path

#import xml.etree.ElementTree as ET
from lxml import etree  as ET
from lxml import objectify


class XmlAdjuster:
    
    def __init__(self,jobGenModules):
        self.cf = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
    
    def __call__(self, generator, inputFile, outputFile, configDict, lastConfigDicts, **kwargs):
        
        """ 
            Template configurator:
            This is a simple xml adjuster which lets you modify xmls by a list of transformations
            This tool does not yet configure the file additionally with the configDict like  the dictionaryAdjuster
            this should be implemented as a pipe of different adjusters, first DictionaryAdjuster then, XmlAdjuster for example
            
            Of course XSLT could be used here, but this is overkill (lxml would support this in python)
        """
        
        jobIdx = int(configDict.Job.jobIdx)
        
        overwrite = False
        
        if "overwrite" in kwargs:
            overwrite = kwargs["overwrite"]
            if not isinstance(overwrite,bool):
                raise ValueError("Setting overwrite not a bool!")
        
        transforms = kwargs["transforms"]
        if isinstance(transforms,str):
          # treat is like a path toa json file, open it an load all transforms like {xpath="asd" , "attributes"=[...] }
          raise NameError("Not yet implemented to load a json file here: " , transforms)
          
        # Change XML FILE ===================================================================================    
        #ET.register_namespace('', kwargs["defaultNamespace"]) # code to make output not using any stupid namespace ":ns0"
        # (load xml wile removeing all namespaces!!!)
        print("XmlAdjuster:: adjust  %s  ---->  %s " % (inputFile,outputFile))
        f = open(inputFile, 'r')
        tree = ET.parse(f)
        root = tree.getroot()
        ####    
        for elem in root.getiterator():
            if not hasattr(elem.tag, 'find'): continue  # (1)
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i+1:]
        objectify.deannotate(root, cleanup_namespaces=True)
        ####
        
        for t in transforms:

                print("\tXmlAdjuster: transforming %s ..." % t['xpath'])
                nodes = root.findall(t["xpath"])
                if not nodes:
                    raise ValueError("No nodes found for transform %s" % t)
                
                # change all specified attributes of all nodes
                if "attributes" in t:
                    for key, values in t["attributes"].items():
                        for n in nodes:
                            
                            
                            # if we have a list of values
                            if isinstance(values,list):
                                if(jobIdx >= len(values)):
                                    raise ValueError("To little values in value list: %s for attribute %s" % (values,key))
                                s = str(values[ jobIdx ])
                            
                            # if we have string (always use this)
                            elif isinstance(values,str):
                                s = values
                            else:    
                                raise ValueError("Wrong type to write into XML: %s " % type(values))
                                
                                
                            if key not in n.attrib:
                                raise ValueError("No key %s in node %s in xml %s " % (key,n,inputFile))
                            n.attrib[key] = s # get the jobIdx value in the list
                
        
        # =======================================================================================================
       
        # replace all options still in the xml
        # make all output folders
        d = os.path.dirname(outputFile)
        if not path.exists(d):
            os.makedirs(d)
        
        ET.ElementTree(root).write(outputFile,encoding="utf-8", method='xml', xml_declaration=True)
