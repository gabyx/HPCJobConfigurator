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


function ES(){ echo "$(currTime) :: end.sh: "; }
# save stdout in file descriptor 4
exec 4>&1

if [[ "${Cluster:mailAddress}" != "" ]];  then
    echo "EOM" | mail -s "Job: ${Job:jobName} has finished" "${Cluster:mailAddress}"
fi

exitFunction 0