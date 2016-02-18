# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

#!/usr/bin/env python3 

# Renders a set of input files

import sys
if sys.version_info[0] != 3:
    print("This script is only python3 compatible!")
    exit(1)


import os, subprocess,traceback,shutil

from subprocess import CalledProcessError

from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from attrdict import AttrMap

from HPCJobConfigurator.jobGenerators import commonFunctions as cF

class MyOptParser(ArgumentParser):
    def error(self,msg):
        self.print_help()
        raise ValueError("Error occured: " + msg)

def main():
         
    
    parser = MyOptParser()
    
    try:

        parser.add_argument("-p", "--processFile", dest="processFile", default="./FileMove.xml" ,
                help="""Input .json file with a list of files for moving into place""", metavar="<path>", required=True)
        opts= AttrMap(vars(parser.parse_args()))
      
        print("========================= Move Files ===========================")
        
        if opts.processFile:
            tasks = cF.jsonLoad(opts.processFile);
            for task in tasks:
                try:
                    
                    # avoiding links to links (get the real path resolving all symlinks)
                    # if that is necessary is not known
                    if "from" in task:
                        task["realfrom"] = os.path.realpath(task["from"])
                    
                    print("Task:", task)

                    if task["type"] == "hardlink":
                        try:
                            os.link(task["realfrom"],task["to"] )
                            continue
                        except:
                          task["type"] ="symlink"
                           
                    if task["type"] == "symlink":
                        try:
                            os.symlink(task["realfrom"],task["to"] )
                            continue
                        except:
                            task["type"] ="copy"
                    
                    if task["type"] == "copy":
                        shutil.copy2(task["from"],task["to"])
                        continue
                        
                    if task["type"] == "makeDirs" :
                        os.makedirs(task["dir"],exist_ok=True)
                        continue
                    
                    
                    raise ValueError("Type: %s not supported!" % str(task))
                    
                except:
                    raise ValueError("Could not execute task: %s" % str(task))
                    
        print("================================================================")  

    except Exception as e:
        print("====================================================================")
        print("Exception occured: " + str(e))
        print("====================================================================")
        traceback.print_exc(file=sys.stdout)
        return 1

    return 0
    

if __name__ == "__main__":
   sys.exit(main());
