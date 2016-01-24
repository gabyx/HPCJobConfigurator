# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

 


logFile="${Job:scriptDir}/endLog.log"
:> $logFile


exitFunc(){

    # Send email
    if [[ "${Cluster:mailAddress}" != "" ]]; then
        cat $logFile | mail -s "Job: ${Job:jobName} has finished" ${Cluster:mailAddress}
    fi

    exit $1
}

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exitFunc 111; }
try() { "$@" || die "cannot $*"; }


executeFilevalidation(){
    # assemble pipeline status
    PYTHONPATH=${General:configuratorModulePath}
    export PYTHONPATH

    python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
        --searchDir="${Pipeline-PostProcess:validationSearchDir}" \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validateOnlyLastModified=True \
        --statusFolder "${Pipeline-PostProcess:statusFolder}" \
        --validationFileInfo  "${Pipeline-PreProcess:validationInfoFile}" \
        --output="${Pipeline-PostProcess:validationInfoFile}"  \
        >> $logFile 2>&1
        
    return $?
}

try executeFilevalidation


#echo "Change directory to ${Job:globalDir}" >> $logFile
#cd ${Job:globalDir}
#try python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorRigidBodyRender.scripts.fileMove \
#-p "{Pipeline-PreProcess:fileMoverGlobalPostProcessFile}" 
##>> $logFile 2>&1 




exitFunc 0
