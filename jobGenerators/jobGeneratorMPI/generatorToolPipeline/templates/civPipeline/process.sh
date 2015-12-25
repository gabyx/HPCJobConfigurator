# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

#!/bin/bash

ES="process.sh:"

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; cleanup ; exit 111 ; }
try() { "$@" || die "Rank: ${Job:processIdxVariabel}: cannot $*"; }


function trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}

function cleanup(){
    echo "$ES Rank: ${Job:processIdxVariabel}: do cleanup!"
    ${Pipeline:cleanUpCommand}
    
    # remove process temporary directory
    echo "$ES Rank: ${Job:processIdxVariabel}: remove temp directory: ${Job:processDir}/temp"
    rm -r ${Job:processDir}/temp > /dev/null 2>&1
}

function handleSignal() {
    echo "$ES Rank: ${Job:processIdxVariabel}: Signal $1 catched, cleanup and exit."
    cleanup 
    exit 0
}

# Setup the Trap
trap_with_arg handleSignal SIGINT SIGTERM SIGUSR1 SIGUSR2


if [[ -z "${Job:processIdxVariabel}" ]]; then
    echo "$ES Rank not defined! "
    exit 1
fi

rm -fr ${Job:processDir} > /dev/null 2>&1
try mkdir -p ${Job:processDir}
cd ${Job:processDir}


# Process Stuff ===================================================================================================================


logFile="${Job:processDir}/processLog.log"
:> $logFile


# Set important PYTHON stuff
export PYTHONPATH=${General:modulePathJobGen}
# matplotlib directory
export MPLCONFIGDIR=${Job:processDir}/temp/matplotlib
try mkdir -p $MPLCONFIGDIR

executeFileMove(){
    python -m JobGenerator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.fileMove \
        -p "$fileMoverProcessFile" >> $logFile 2>&1 
    return $?
}

echo "File Mover =======================================================" >> $logFile
echo "Search file move process file ..." >> $logFile
fileMoverProcessFile=$( python3 -c "print(\"${Pipeline-PreProcess:fileMoverProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$fileMoverProcessFile" ]; then
    echo "File mover process file (.xml) not found! It seems we are finished moving files! (file: $fileMoverProcessFile)" >> $logFile
    
else
    echo "File mover process file : $fileMoverProcessFile" >> $logFile
    echo "Start moving files" >> $logFile
    echo "Change directory to ${Job:processDir}" >> $logFile
    cd ${Job:processDir}

    begin=$(date +"%s")
    try executeFileMove
    termin=$(date +"%s")
    difftimelps=$(($termin-$begin))
    echo "File mover statistics: $(($difftimelps / 60)) minutes and $(($difftimelps % 60)) seconds elapsed." >> $logFile  
      
fi
echo "==================================================================" >> $logFile
cd ${Job:processDir}


executeConverter(){
    python -m JobGenerator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generalPipeline.generalProcess \
        -p "$converterProcessFile"   >> $logFile 2>&1 
    return $?
}

echo "Converter ========================================================" >> $logFile
echo "Search converter process file ..." >> $logFile
converterProcessFile=$( python3 -c "print(\"${Pipeline:converterProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$converterProcessFile" ]; then
    echo "Converter process file (.xml) not found! It seems we are finished converting! (file: $converterProcessFile)" >> $logFile
    
else
    echo "Converter process file : $converterProcessFile" >> $logFile
    echo "Start converting the files" >> $logFile
    echo "Change directory to ${Pipeline:converterExecutionDir}" >> $logFile
    cd ${Pipeline:converterExecutionDir}
    
    begin=$(date +"%s")
    try executeConverter
    termin=$(date +"%s")
    difftimelps=$(($termin-$begin))
    echo "Converter statistics: $(($difftimelps / 60)) minutes and $(($difftimelps % 60)) seconds elapsed." >> $logFile  
      
fi
echo "==================================================================" >> $logFile
cd ${Job:processDir}


executeCorrelator(){
    python -m JobGenerator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generalPipeline.generalProcess \
        -p "$correlatorProcessFile"   >> $logFile 2>&1 
    return $?
}

echo "Correlator =======================================================" >> $logFile
echo "Search correlator process file ..." >> $logFile
correlatorProcessFile=$( python3 -c "print(\"${Pipeline:correlatorProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$correlatorProcessFile" ]; then
    echo "Correlator process file (.xml) not found! It seems we are finished correlatoring! (file: $correlatorProcessFile)" >> $logFile
else
    echo "Correlator process file : $correlatorProcessFile" >> $logFile
    echo "Start correlating the files" >> $logFile
    echo "Change directory to ${Pipeline:correlatorExecutionDir}" >> $logFile
    cd ${Pipeline:correlatorExecutionDir}
    
    begin=$(date +"%s")
    try executeCorrelator
    termin=$(date +"%s")
    difftimelps=$(($termin-$begin))
    echo "correlator statistics: $(($difftimelps / 60)) minutes and $(($difftimelps % 60)) seconds elapsed." >> $logFile    
            
fi
echo "================================================================== " >> $logFile
cd ${Job:processDir}

echo "Final cleanup ====================================================" >> $logFile
cleanup
echo "================================================================== " >> $logFile


exit 0 

# =======================================================================================================================================
