#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================


ES="process.sh: Rank: ${Job:processIdxVariabel}:"

thisPID="$BASHPID"

stage=0
signalReceived="False"
cleaningUp="False"



function exitFunction(){
    echo "Exiting $ES exit code: $1 (0=success), stage: ${stage}"
    #if [[ ${signalReceived} == "True" ]]; then
      ## http://www.cons.org/cracauer/sigint.html
      ## kill ourself to signal calling process that we exited on signal
      #trap - SIGINT
      #kill -s SIGINT ${thisPID}
    #else
      exit $1
    #fi
}

function trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}

function executeFileValidation(){
    # assemble pipeline status
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH

    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --searchDirNew="${processDir}" \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validateOnlyLastModified=True \
        --output="${Pipeline:validationInfoFile}"
        
    return $?
}

function cleanup(){
    if [[ "${cleaningUp}" == "True" ]] ; then
        # we are already cleaning up
        return 0
    else
        cleaningUp="True"
    fi
    
    echo "$ES do cleanup! =============" 
    cd ${processDir}
    ${Pipeline:cleanUpCommand}
    if [[ ${stage} -eq 2 ]]; then
      executeFileValidation
      echo "$ES fileValidation exitStatus: $?"
    fi
    echo "$ES cleanup finished ========"
}

function ignoreAllSignals(){
    echo "$ES already shutting down: ignoring signal: $1"
}
function shutDownHandler() {
    # ignore all signals
    trap_with_arg ignoreAllSignals SIGINT SIGUSR1 SIGUSR2 SIGTERM
    
    signalReceived="True"
    if [[ "${cleaningUp}" == "False" ]]; then
      echo "$ES Signal $1 catched, cleanup and exit."
      cleanup
      exitFunction 0
    else
      echo "$ES Signal $1 catched, we are already cleaning up, continue."
    fi
}

function printTime(){
    dt=$(echo "$2 - $1" | bc)
    dd=$(echo "$dt/86400" | bc)
    dt2=$(echo "$dt-86400*$dd" | bc)
    dh=$(echo "$dt2/3600" | bc)
    dt3=$(echo "$dt2-3600*$dh" | bc)
    dm=$(echo "$dt3/60" | bc)
    ds=$(echo "$dt3-60*$dm" | bc)
    printf "$ES Time Elapsed: %d:%02d:%02d:%02.4f\n" $dd $dh $dm $ds
}
function launchInForeground(){
  start=$(date +%s.%N) ;
  "$@"
  res=$?      
  end=$(date +%s.%N) ;
  printTime $start $end ;
  return $res  
}

yell() { echo "$0: $*" >&2; }
die() { yell "$1"; cleanup ; exitFunction 111 ; }
try() { "$@" || die "$ES cannot $*" ; }
dieNoCleanUp() { yell "$1"; exitFunction 111 ; }
tryNoCleanUp() { "$@" || die "$ES cannot $*" ;  }

# Setup the Trap
# Be aware that SIGINT and SIGTERM will be catched here, but if this script is run with mpirun
# mpirun will forward SIGINT/SIGTERM and then quit, leaving this script still running in the signal handler
trap_with_arg shutDownHandler SIGINT SIGUSR1 SIGUSR2 SIGTERM


if [[ -z "${Job:processIdxVariabel}" ]]; then
    echo "Rank not defined! "
    exitFunction 111
fi

rm -fr "${Job:processDir}"
tryNoCleanUp mkdir -p "${Job:processDir}"

# Save processDir, it might be relative! and if signal handler runs 
# using a relative path is not good
cd "${Job:processDir}"
processDir=$(pwd)

# put stdout and stderr into logFile
logFile="${processDir}/processLog.log"
#http://stackoverflow.com/a/18462920/293195
exec 3>&1 1>>${logFile} 2>&1

stage=0
echo "File Mover =======================================================" 
echo "Search file move process file ..."
fileMoverProcessFile=$( python3 -c "print(\"${Pipeline-PreProcess:fileMoverProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$fileMoverProcessFile" ]; then
    echo "File mover process file (.xml) not found! It seems we are finished moving files! (file: $fileMoverProcessFile)" 
else
    echo "File mover process file : $fileMoverProcessFile" 
    echo "Start moving files" 
    echo "Change directory to ${processDir}" 
    cd ${processDir}

    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH

    try launchInForeground python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.fileMove \
        -p "$fileMoverProcessFile"
        
fi
echo "==================================================================" 

cd ${processDir}

stage=1
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
    begin=$(date +"%s")
    try launchInForeground ${Pipeline:executableConverter} renderer \
        -i $converterProcessFile \
        -r renderman \
        -s ${Pipeline:sceneFile} \
        -m ${Pipeline:mediaDir} \
        -c ${Pipeline:converterLogic}

fi
echo "==================================================================" 

cd ${processDir}

stage=2
echo "Render ===========================================================" 
echo "Search render process file ..." 
renderProcessFile=$( python3 -c "print(\"${Pipeline:renderProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$renderProcessFile" ]; then
    echo "Render process file (.xml) not found! It seems we are finished rendering! (file: $renderProcessFile)" 
else
    echo "Render process file : $renderProcessFile" 
    echo "Start rendering the files" 
    echo "Change directory to ${Pipeline:renderExecutionDir}" 
    cd ${Pipeline:renderExecutionDir}
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH

    try launchInForeground python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.renderPipeline.renderFrames \
        -p "$renderProcessFile" \
        -c "${Pipeline:executableRenderer}"
            
fi
echo "================================================================== " 

cd ${processDir}

echo "Final cleanup ====================================================" 
cleanup
echo "================================================================== " 


exit 0 
