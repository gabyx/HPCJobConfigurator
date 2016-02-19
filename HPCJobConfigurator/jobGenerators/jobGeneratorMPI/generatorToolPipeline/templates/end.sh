#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

function currTime(){ date +"%H:%M:%S" }
function ES(){ echo "$(currTime) :: process.sh: Rank: ${Job:processIdxVariabel}" }

logFile="${Job:scriptDir}/endLog.log"
> $logFile


yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }


#  Validate all files in process folder
#  each process validates 
#
function executeFileValidationPerProcess(){
    # assemble pipeline status
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH
    
    # put stdout and stderr into logFile
    procLogFile="${Pipeline-PostProcess:validationSearchDirProcesses}/processLog.log"
    
    echo "$(ES) File validation: per Process =============" 1>>${procLogFile}
    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --searchDirNew="${Pipeline-PostProcess:validationSearchDirProcesses}" \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validateOnlyLastModified=True \
        --output="${Pipeline-PostProcess:validationInfoFileProcess}" 1>>${procLogFile} 2>&1
    
    echo "$(ES) ==========================================" 1>>${procLogFile}
        
    return $?
}



# Collects all FileInfos in each Process folder
# compares to the old FileInfo from last job
# writes a new output FileInfo for this job
executeFilevalidation(){
    # assemble pipeline status
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH
    
    echo "$(ES) File validation: combine from Process ====" 1>>${logFile}
    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --valFileInfoGlobNew "${Pipeline-PostProcess:validationInfoFilesProcessesGlob}" \
        --valFileInfoGlobOld "${Pipeline-PreProcess:validationInfoFile}" \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validateOnlyLastModified=True \
        --statusFolder "${Pipeline-PostProcess:statusFolder}" \
        --output="${Pipeline-PostProcess:validationInfoFile}"  \
        >> $logFile 2>&1
        
    echo "$(ES) ==========================================" 1>>${logFile}
    
    return $?
}

# Validates all files in the job folder (over all processes)
# compares to the old FileInfo from last job
# writes a new output FileInfo for this job
executeFilevalidationAll(){
    # assemble pipeline status
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH
    
    echo "$(ES) File validation: validate all files (manual) ===" 1>>${logFile}
    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --searchDirNew "${Pipeline-PostProcess:validationSearchDirAll}" \
        --valFileInfoGlobOld "${Pipeline-PreProcess:validationInfoFile}" \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validateOnlyLastModified=True \
        --statusFolder "${Pipeline-PostProcess:statusFolder}" \
        --output="${Pipeline-PostProcess:validationInfoFile}"  \
        >> $logFile 2>&1
        
    echo "$(ES) ================================================" 1>>${logFile}
        
    return $?
}

# parallel validation ==================================================

# validate file in global process folder -> FileInfos per Process
# mpirun -np ${Cluster:nProcesses} executeFileValidationPerProcess

# combine FileInfos into one
executeFilevalidation

# ======================================================================

# manual validation if normal one failed ===============================
# manually validate all files (use this function if executeFilevalidation failed)
#try executeFilevalidationAll
# ======================================================================


# Send email
if [[ "${Cluster:mailAddress}" != "" ]]; then
    cat $logFile | mail -s "Job: ${Job:jobName} has finished" ${Cluster:mailAddress}
fi

exit 0
