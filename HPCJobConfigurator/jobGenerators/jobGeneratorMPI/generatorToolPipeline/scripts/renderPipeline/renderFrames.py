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


import os, subprocess,traceback
from subprocess import CalledProcessError

from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from attrdict import AttrMap

from HPCJobConfigurator.jobGenerators.importHelpers import ImportHelpers as iH
from HPCJobConfigurator.jobGenerators.commonFunctions import CommonFunctions as cf


class MyOptParser(ArgumentParser):
    def error(self,msg):
        self.print_help()
        raise ValueError("Error occured: " + msg)

def main():
         
    
    parser = MyOptParser()
    
    try:
        

        parser.add_argument("-c", "--renderCommand", dest="renderCommand", default="prman -t:1" ,
                help="""The render command to call.""", metavar="<path>", required=True)         
        
        parser.add_argument("-p", "--processFile", dest="processFile", default="./RenderProcess.xml" ,
                help="""Input file xml path with a list of files for rendering""", metavar="<path>", required=True)
        
           
        opts= AttrMap(vars(parser.parse_args()))
      
        print("================== Rendering Frames ============================")
        
        if(opts.processFile):
            frames = cf.jsonLoad(opts.processFile);

            if not frames:
                raise ValueError("No frames specified in xml %s" % opts.processFile)
            
            for f in frames:
                print("Render frame: %s " % f["inputFile"])
                command = opts.renderCommand.split(" ") + [f["inputFile"]]
                print("Command: %s" % str(" ".join(command)))
                try:
                    out = subprocess.check_output(command, stderr=subprocess.STDOUT)
                    print("Render command output: %s" % out)
                except CalledProcessError as c:
                    print("Rendering Process Error: for file: %s with render output: %s " % (f,c.output) )
                    print("Continue to next frame ...")
        print("================================================================")        
            

    except Exception as e:
        print("====================================================================", file=sys.stderr)
        print("Exception occured: " + str(e), file=sys.stderr)
        print("====================================================================", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1
    
    print("================== Rendering finished ==================== ")
    return 0
    

if __name__ == "__main__":
   sys.exit(main());