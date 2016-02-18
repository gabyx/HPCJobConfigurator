# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os,sys,traceback,signal

from attrdict import AttrMap
from argparse import ArgumentParser

from HPCJobConfigurator.jobGenerators.importHelpers import ImportHelpers as iH
from HPCJobConfigurator.jobGenerators.commonFunctions import CommonFunctions as cf

class MyOptParser(ArgumentParser):
    def error(self,msg):
        self.print_help()
        raise ValueError("Error occured: " + msg)


def main():

    try: 
        parser = MyOptParser()
        parser.add_argument("-p","--processFile", dest="processFile", default="" ,
                help="""Json file with process description.""", metavar="<path>", required=True)    
        
        
        opts= AttrMap(vars(parser.parse_args()))
          
        if(opts.processFile):
            
            processFile = cf.jsonLoad(opts.processFile);

            # load process module/class
            mod, ProcessClass = iH.importClassFromModule( **processFile["processClass"] )

            process = ProcessClass( processFile, jobGenModules = {"importHelpers":iH, "commonFunctions" : cf} )
            process.doProcessing()
           
        return 0
            
    except Exception as e:
        sys.stdout.flush()
        print("====================================================================", file=sys.stderr)
        print("Exception occured here: " + str(e), file=sys.stderr)
        print("====================================================================", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == "__main__":
  sys.exit(main());