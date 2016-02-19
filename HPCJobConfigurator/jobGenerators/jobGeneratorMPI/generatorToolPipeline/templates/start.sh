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
function ES(){ echo "$(currTime) :: start.sh: " }

    
yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }


logFile="${Job:scriptDir}/startLog.log"
> $logFile

# preperation for render job
PYTHONPATH=${General:configuratorModulePath}
export PYTHONPATH
try python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.prepareToolPipeline  \
        --pipelineSpecs="${Pipeline:pipelineSpecs}" \
        --validationFileInfo  "${Pipeline-PreProcess:validationInfoFile}"\
        --processes ${Cluster:nProcesses} \
        >> $logFile 2>&1


if [[ "${Cluster:mailAddress}" != "" ]] ;  then
    cat $logFile | mail -s "Job: ${Job:jobName} has started" ${Cluster:mailAddress}
fi

echo "$(ES) Make global dir ${Job:globalDir}" >> $logFile 2>&1 
try mkdir -p "${Job:globalDir}"


exit 0
