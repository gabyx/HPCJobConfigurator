# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

    

ES="start.sh:"


yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 1 ; }
try() { "$@" || die "cannot $*"; }



if [[ "${Cluster:mailAddress}" != "" ]] ;  then
    echo "EOM" | mail -s "Job: ${Job:jobName} has started" ${Cluster:mailAddress} 
fi

#echo "Make global dir ${Job:globalDir}" 
try mkdir -p ${Job:globalDir} 



exit 0
