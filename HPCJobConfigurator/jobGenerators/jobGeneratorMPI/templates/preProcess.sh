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

function ES(){ echo "$(currTime) :: preProcess.sh: Rank: ${Job:processIdxVariabel}"; }
# save stdout in file descriptor 4
exec 4>&1

echo "$(ES) Remove and Make Directory:  ${Job:localDir}"
rm -r "${Job:localDir}" > /dev/null 2>&1
tryNoCleanUp mkdir -p "${Job:localDir}"

if [[ "${Job:copyLocation}" != "" ]]; then
    echo "$(ES) Create: temp folder" 
    tryNoCleanUp mkdir -p "${Job:localDir}/temp"
    echo "$(ES) Copy files to node"
    tryNoCleanUp cp -r "${Job:copyLocation}" "${Job:localDir}/temp/"
fi

exitFunction 0
