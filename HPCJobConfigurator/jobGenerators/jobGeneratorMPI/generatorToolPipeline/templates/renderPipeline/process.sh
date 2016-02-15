#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================


ES="process.sh:"

# store initial stdout to 3
exec 3>&1 

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; cleanup ; exit 111 ; }
try() { "$@" || die "Rank: ${Job:processIdxVariabel}: cannot $*"; }

# trap echo gets redirected to initial stdout =  3
function trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig 1>&3" "$sig"
    done
}

function cleanup(){
    echo "$ES Rank: ${Job:processIdxVariabel}: do cleanup! ============="
    ${Pipeline:cleanUpCommand}
    echo "$ES Rank: ${Job:processIdxVariabel}: cleanup finished ========"
    exit $1
}

function handleSignal() {
    echo "$ES Rank: ${Job:processIdxVariabel}: Signal $1 catched, cleanup and exit."
    cleanup 0
}

# Setup the Trap
trap_with_arg handleSignal SIGINT SIGTERM SIGUSR1 SIGUSR2


if [[ -z "${Job:processIdxVariabel}" ]]; then
    echo "Rank not defined! "
    exit 1
fi


rm -fr ${Job:processDir}
try mkdir -p ${Job:processDir}
cd ${Job:processDir}

logFile="${Job:processDir}/processLog.log"
:> $logFile


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

    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH
    
    begin=$(date +"%s")
    try python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.fileMove \
        -p "$fileMoverProcessFile" >> $logFile 2>&1 
    
    termin=$(date +"%s")
    difftimelps=$(($termin-$begin))
    echo "File mover statistics: $(($difftimelps / 60)) minutes and $(($difftimelps % 60)) seconds elapsed." >> $logFile  
      
fi
echo "==================================================================" >> $logFile

cd ${Job:processDir}

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
    try ${Pipeline:executableConverter} renderer\
        -i $converterProcessFile \
        -r renderman \
        -s ${Pipeline:sceneFile} \
        -m ${Pipeline:mediaDir} \
        -c ${Pipeline:converterLogic} >> $logFile 2>&1 
    
    termin=$(date +"%s")
    difftimelps=$(($termin-$begin))
    echo "Converter statistics: $(($difftimelps / 60)) minutes and $(($difftimelps % 60)) seconds elapsed." >> $logFile  
      
fi
echo "==================================================================" >> $logFile


cd ${Job:processDir}


echo "Render ===========================================================" >> $logFile
echo "Search render process file ..." >> $logFile
renderProcessFile=$( python3 -c "print(\"${Pipeline:renderProcessFile}\".format(${Job:processIdxVariabel}))" )

if [ ! -f "$renderProcessFile" ]; then
    echo "Render process file (.xml) not found! It seems we are finished rendering! (file: $renderProcessFile)" >> $logFile
else
    echo "Render process file : $renderProcessFile" >> $logFile
    echo "Start rendering the files" >> $logFile
    echo "Change directory to ${Pipeline:renderExecutionDir}" >> $logFile
    cd ${Pipeline:renderExecutionDir}
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH
    
    begin=$(date +"%s")
    
    try python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.renderPipeline.renderFrames \
        -p "$renderProcessFile" \
        -c "${Pipeline:executableRenderer}" >> $logFile 2>&1 
        
    termin=$(date +"%s")
    difftimelps=$(($termin-$begin))
    echo "Render statistics: $(($difftimelps / 60)) minutes and $(($difftimelps % 60)) seconds elapsed." >> $logFile    
            
fi
echo "================================================================== " >> $logFile

cd ${Job:processDir}

echo "Final cleanup ====================================================" >> $logFile
cleanup
echo "================================================================== " >> $logFile


exit 0 
