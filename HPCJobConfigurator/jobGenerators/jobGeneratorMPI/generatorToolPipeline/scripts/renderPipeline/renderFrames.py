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


import os, subprocess,traceback, signal ,datetime
from subprocess import CalledProcessError

from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from attrdict import AttrMap

from HPCJobConfigurator.jobGenerators import importHelpers as iH
from HPCJobConfigurator.jobGenerators import commonFunctions as cF


def headerStr(){
  return datetime.datetime.now().time().isoformat() + " :: renderFrames.py: "
}


class MyOptParser(ArgumentParser):
    def error(self,msg):
        self.print_help()
        raise ValueError("Error occured: " + msg)


subProcess = None
shutDown = False

def shutDownHandler(signum,frame):
  global shutDown, subProcess
  
  if not shutDown:
    
    shutDown=True
    print(headerStr() + "catched signal: ", signum)
    if subProcess is not None:
      print(headerStr() + "send SIGTERM to pid: ", subProcess.pid);
      try:
        subProcess.send_signal(signal.SIGTERM)
      except OSError as err:
        print(headerStr() + "could not send signal to subProcess, probably already terminated"); 
        
  else:
    print(headerStr() + "ignoring catched signal: %i, shutdown flag already set" % signum)
    return
    
  
  
# we catch SIGINT/SIGUSR2/SIGTERM which all aboard the rendering
signal.signal(signal.SIGINT, shutDownHandler)
signal.signal(signal.SIGUSR2, shutDownHandler)
signal.signal(signal.SIGTERM, shutDownHandler)

def main():
    
    global subProcess,shutdown
    
    parser = MyOptParser()
    
    try:
        
        parser.add_argument("-c", "--renderCommand", dest="renderCommand", default="prman -t:1" ,
                help="""The render command to call.""", metavar="<path>", required=True)         
        
        parser.add_argument("-p", "--processFile", dest="processFile", default="./RenderProcess.xml" ,
                help="""Input file xml path with a list of files for rendering""", metavar="<path>", required=True)
        
           
        opts= AttrMap(vars(parser.parse_args()))
      
        print("================== Rendering Frames =========================")
        print("Script: " + __file__ )
        
        if(opts.processFile):
            frames = cF.jsonLoad(opts.processFile);

            if not frames:
                raise ValueError("No frames specified in xml %s" % opts.processFile)
            
            for f in frames:
              
                if shutDown:
                  break
                  
                print("Render frame: %s " % f["inputFile"])
                command = opts.renderCommand.split(" ") + [f["inputFile"]]
                print("Command: %s" % str(" ".join(command)))
                sys.stdout.flush()
                
                try:
                  subProcess = subprocess.Popen(command, stderr=subprocess.STDOUT)
                  # Waiting for process
                  subProcess.wait()
                  subProcess = None
                  
                except Exception as c:
                  raise NameError("Rendering Process Error: for file: %s with render output: %s " % (f,c.output) )
                  
        if shutDown:
            print("Render Loop shutdown")
        
        print("============================================================")        
            

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