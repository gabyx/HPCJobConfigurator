#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

# Source all common functions
source ${General:configuratorModuleDir}/jobGenerators/jobGeneratorMPI/scripts/commonFunctions.sh

if [[ -z "${Job:processIdxVariabel}" ]]; then
    echo "Rank not defined! "
    exitFunction 111
fi

function ES(){ echo "$(currTime) :: process.sh: Rank: ${Job:processIdxVariabel}"; }

executionDir=$(pwd)
thisPID="$BASHPID"
stage=0
signalReceived="False"
cleaningUp="False"


function cleanup(){
  echo "$(ES) nothing to cleanup!"
}

function shutDownHandler() {
    # ignore all signals
    trap_with_arg ignoreSignal SIGINT SIGUSR1 SIGUSR2 SIGTERM
    
    signalReceived="True"
    if [[ "${cleaningUp}" == "False" ]]; then
      echo "$(ES) Signal $1 catched, cleanup and exit."
      cleanup
      exitFunction 0
    else
      echo "$(ES) Signal $1 catched, we are already cleaning up, continue."
    fi
}

if [[ -z "${Job:processIdxVariabel}" ]]; then
    echo "$(ES) Rank not defined! "
    exit 1
fi

# Setup the Trap
# Be aware that SIGINT and SIGTERM will be catched here, but if this script is run with mpirun
# mpirun will forward SIGINT/SIGTERM and then quit, leaving this script still running in the signal handler
trap_with_arg shutDownHandler SIGINT SIGUSR1 SIGUSR2 SIGTERM SIGPIPE

# Process folder ================================
tryNoCleanUp mkdir -p "${Job:processDir}"

# Save processDir, it might be relative! and if signal handler runs 
# using a relative path is not good
cd "${Job:processDir}"
processDir=$(pwd)
# ========================================================

# Output rerouting =======================================
# save stdout in file descriptor 4
exec 4>&1
# put stdout and stderr into logFile
logFile="${processDir}/processLog.log"
#http://stackoverflow.com/a/18462920/293195
exec 3>&1 1>>${logFile} 2>&1
# filedescriptor 3 is still connected to the console
# ========================================================

echo "$(ES) starting executable ..."

tryNoCleanUp ${Job:executableCommand}

exitFunction 0
