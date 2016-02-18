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



class CopyAdjuster:
    
    def __init__(self,jobGenModules):
        self.cF = jobGenModules["commonFunctions"]
        self.iH = jobGenModules["importHelpers"]
    
    def __call__(self, generator, inputFile, outputFile,*args,**kwargs):
        
        """ 
            Template configurator:
            Simply copy the file to the output destination 
        """
        overwrite = False
        
        if "overwrite" in kwargs:
            overwrite = kwargs["overwrite"]
            if not isinstance(overwrite,bool):
                raise ValueError("Setting overwrite not a bool!")
                
        if not overwrite and os.path.exists(outputFile):
            print("CopyAdjuster:: File %s  exists, -> no overwrite!" % inputFile)
            return
        
        
        # make all output folders
        d = os.path.dirname(outputFile)
        if not path.exists(d):
            os.makedirs(d)
        
        # avoiding links to links (get the real path resolving all symlinks)
        # if that is necessary is not known
        inputFile = os.path.realpath(inputFile)

        t = None
        if "type" in kwargs:
            t = kwargs["type"]
        
        if t == "hardlink":
            print("CopyAdjuster:: hardlink  %s  ---->  %s " % (inputFile,outputFile))
            os.link(inputFile,outputFile)
        elif t == "symlink":
            print("CopyAdjuster:: link  %s  ---->  %s " % (inputFile,outputFile))
            os.symlink(inputFile,outputFile)
        elif t == "copy":
            print("CopyAdjuster:: copy  %s  ---->  %s " % (inputFile,outputFile))
            shutil.copy2(inputFile,outputFile)
        else:
            raise ValueError("type: %s not defined for copying file %s" % (t,inputFile))
        
        
