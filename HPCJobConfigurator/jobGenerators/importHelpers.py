# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import importlib

from HPCJobConfigurator.jobGenerators import commonFunctions as cF

def importClassFromModule(moduleName, className, modulePath=None):
    
    if modulePath :
        loader = importlib.machinery.SourceFileLoader(moduleName, path=modulePath)
        mod = loader.load_module()
    else: 
        # no path given, try normal import
        try:
          mod = __import__(moduleName)
        except:
          raise ValueError("No module with name %s found!" % moduleName) 
    # get class
    components = moduleName.split('.')
    try:
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod, getattr(mod,className)
        
    except AttributeError as e:
        print("Module: %s with type: %s " % (str(mod),type(mod)) )
        raise e
    

def importClassFromModuleString(s, verbose=False):
    
    if isinstance(s,str):
        s = s.strip()
        
        if(s[0] == "{"):
            # json string
            s = cF.jsonParse(s)
            if verbose:
                print("Load class: %s in module: %s" % (s["className"],s["moduleName"]) ) 
            return ImportHelpers.importClassFromModule(**s)
        
        # normal string e.g.: JobGenerator.jobGenerators.jobGeneratorMPI.RigidBodySim 
        comps = s.split(".")
        clName =  comps[-1]
        mdName = ".".join(comps[0:-1])
        
        if verbose:
          print("Load class: %s in module: %s" % (clName,mdName) ) 
          
        return importClassFromModule(moduleName=mdName,className=clName)
        
    elif isinstance(s,dict):
        
        if verbose:
          print("Load class: %s in module: %s" % (s["className"],s["moduleName"]) ) 
          
        return importClassFromModule(**s)
        
    else:
      raise NameError("Could no load module by string: %s" % s)
      

    
    
