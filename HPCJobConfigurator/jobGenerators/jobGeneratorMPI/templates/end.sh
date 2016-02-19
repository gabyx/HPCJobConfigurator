#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

 
function currTime(){ date +"%H:%M:%S.%3N" ; }
function ES(){ echo "$(currTime) :: end.sh: "; }


if [[ "${Cluster:mailAddress}" != "" ]];  then
    echo "EOM" | mail -s "Job: ${Job:jobName} has finished" "${Cluster:mailAddress}"
fi

exit 0