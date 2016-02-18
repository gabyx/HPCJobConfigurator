#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================


logFile="${Job:scriptDir}/endLog.log"
> $logFile


yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }


# Collects all FileInfos in each Process folder
# compares to the old FileInfo from last job
# writes a new output FileInfo for this job
executeFilevalidation(){
    # assemble pipeline status
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH

    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --valFileInfoGlobNew "${Pipeline-PostProcess:validationInfoFilesProcessesGlob}" \
        --valFileInfoGlobOld "${Pipeline-PreProcess:validationInfoFile}" \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validateOnlyLastModified=True \
        --statusFolder "${Pipeline-PostProcess:statusFolder}" \
        --output="${Pipeline-PostProcess:validationInfoFile}"  \
        >> $logFile 2>&1
        
    return $?
}

# Validates all files in the job folder (over all processes)
# compares to the old FileInfo from last job
# writes a new output FileInfo for this job
executeFilevalidationAll(){
    # assemble pipeline status
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH

    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --searchDirNew "${Pipeline-PostProcess:validationSearchDir}" \
        --valFileInfoGlobOld "${Pipeline-PreProcess:validationInfoFile}" \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validateOnlyLastModified=True \
        --statusFolder "${Pipeline-PostProcess:statusFolder}" \
        --output="${Pipeline-PostProcess:validationInfoFile}"  \
        >> $logFile 2>&1
        
    return $?
}

# combine FileInfos
# try executeFilevalidation

# manually validate all files (use this function if executeFilevalidation failed)
try executeFilevalidationAll



# Send email
if [[ "${Cluster:mailAddress}" != "" ]]; then
    cat $logFile | mail -s "Job: ${Job:jobName} has finished" ${Cluster:mailAddress}
fi

exit 0
