#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

source ${General:configuratorModuleDir}/jobGenerators/jobGeneratorMPI/scripts/commonFunctions.sh

function ES(){ echo "$(currTime) :: end.sh: Rank: ${Job:processIdxVariabel}"; }

# save stdout in file descriptor 4
exec 4>&1


logFile="${Job:scriptDir}/endLog.log"
> $logFile


# Collects all FileInfos in each Process folder
# compares to the old FileInfo from last job
# writes a new output FileInfo for this job
executeFilevalidation(){
    # assemble pipeline status
    export PYTHONPATH="${General:configuratorModulePath}:$PYTHONPATH"
    
    echo "$(ES) File validation: combine from Process ====" 1>>${logFile}
    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --valFileInfoGlobNew "${Pipeline-PostProcess:validationInfoFilesCombineGlob}" \
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
    export PYTHONPATH="${General:configuratorModulePath}:$PYTHONPATH"
    
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
mpirun -np ${Cluster:nProcesses} ${TemplatesOut:endPerProcess}

# combine FileInfos into one
executeFilevalidation

# ======================================================================

# manual validation if normal one failed ===============================
# manually validate all files (use this function if executeFilevalidation failed)
#tryNoCleanUp executeFilevalidationAll
# ======================================================================


# Send email
if [[ "${Cluster:mailAddress}" != "" ]]; then
    cat $logFile | mail -s "Job: ${Job:jobName} has finished" ${Cluster:mailAddress}
fi

exit 0
