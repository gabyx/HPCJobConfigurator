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
    
    echo "$ES Rank: ${Job:processIdxVariabel}: do cleanup!  ============"
    cd ${executionDir}
    ${Pipeline:cleanUpCommand}
    
    # remove process temporary directory
    echo "$ES Rank: ${Job:processIdxVariabel}: remove temp directory: ${processDir}/temp"
    rm -r ${processDir}/temp > /dev/null 2>&1
    
    echo "$ES Rank: ${Job:processIdxVariabel}: cleanup finished ========"
}

function handleSignal() {
    echo "$ES Rank: ${Job:processIdxVariabel}: Signal $1 catched, cleanup and exit."
    cleanup
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


# Process Stuff ===================================================================================================================

# Set important PYTHON stuff
export PYTHONPATH="${General:configuratorModulePath}:$PYTHONPATH"
# matplotlib directory
export MPLCONFIGDIR=${Job:processDir}/temp/matplotlib
try mkdir -p $MPLCONFIGDIR

executeFileMove(){
    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.fileMove \
        -p "$fileMoverProcessFile" 
    return $?
}

echo "File Mover =======================================================" 
echo "Search file move process file ..." 
fileMoverProcessFile=$( python3 -c "print(\"${Pipeline-PreProcess:fileMoverProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$fileMoverProcessFile" ]; then
    echo "File mover process file (.xml) not found! It seems we are finished moving files! (file: $fileMoverProcessFile)" 
    
else
    echo "File mover process file : $fileMoverProcessFile"
    echo "Start moving files" 
    echo "Change directory to ${Job:processDir}"
    cd ${processDir}

    try launchInForeground python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.fileMove \
        -p "$fileMoverProcessFile"  
      
fi
echo "==================================================================" 
cd ${processDir}


executeConverter(){
    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generalPipeline.generalProcess \
        -p "$converterProcessFile"    2>&1 
    return $?
}

echo "Converter ========================================================" 
echo "Search converter process file ..." 
converterProcessFile=$( python3 -c "print(\"${Pipeline:converterProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$converterProcessFile" ]; then
    echo "Converter process file (.xml) not found! It seems we are finished converting! (file: $converterProcessFile)" 
    
else
    echo "Converter process file : $converterProcessFile" 
    echo "Start converting the files" 
    echo "Change directory to ${Pipeline:converterExecutionDir}" 
    cd ${Pipeline:converterExecutionDir}
    
    try launchInForeground python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generalPipeline.generalProcess \
        -p "$converterProcessFile"
      
fi
echo "==================================================================" 
cd ${processDir}


echo "Correlator =======================================================" 
echo "Search correlator process file ..." 
correlatorProcessFile=$( python3 -c "print(\"${Pipeline:correlatorProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$correlatorProcessFile" ]; then
    echo "Correlator process file (.xml) not found! It seems we are finished correlatoring! (file: $correlatorProcessFile)" 
else
    echo "Correlator process file : $correlatorProcessFile" 
    echo "Start correlating the files" 
    echo "Change directory to ${Pipeline:correlatorExecutionDir}" 
    cd ${Pipeline:correlatorExecutionDir}
    
    try launchInForeground python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generalPipeline.generalProcess \
        -p "$correlatorProcessFile" 
   
            
fi
echo "================================================================== " 
cd ${processDir}

echo "Final cleanup ====================================================" 
cleanup
echo "================================================================== " 


exitFunction 0 

# =======================================================================================================================================
