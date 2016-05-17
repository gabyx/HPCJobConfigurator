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

function ES(){ echo "$(currTime) :: endPerProcess.sh: Rank: ${Job:processIdxVariabel}"; }

# save stdout in file descriptor 4
exec 4>&1

#  Validate all files in process folder
#  each process validates 

export PYTHONPATH="${General:configuratorModulePath}:$PYTHONPATH"

# put stdout and stderr into process logFile
procLogFile="${Pipeline-PostProcess:validationSearchDirProcess}/processLog.log"

echo "$(ES) File validation: per Process =============" 1>>${procLogFile}
python -m HPCJobConfigurator.jobGenerators.jobGeneratorMPI.generatorToolPipeline.scripts.generateFileValidation  \
    --searchDirNew="${Pipeline-PostProcess:validationSearchDirProcess}" \
    --pipelineSpecs="${Pipeline:pipelineSpecs}" \
    --validateOnlyLastModified=True \
    --output="${Pipeline-PostProcess:validationInfoFileProcess}" 1>>${procLogFile} 2>&1

echo "$(ES) ==========================================" 1>>${procLogFile}
    
exitFunction $?

