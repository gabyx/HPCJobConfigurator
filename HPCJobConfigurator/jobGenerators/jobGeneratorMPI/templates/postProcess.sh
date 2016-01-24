#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================



ES="postProcess.sh:"

echo "$ES Move Directory: ${Job:localDir} "

# make dir if it does not yet exist
mkdir -p ${Job:globalDir}

if [[ "${Job:copyLocation}" != "" ]]; then
    echo "$ES Delete temp folder"
    rm -fr ${Job:localDir}/temp/
fi

# dont follow symbolic, links, copy symbolic links as is!
if [[ "${Job:localDir}" != "${Job:globalDir}" ]]; then

    if [[ "${Job:tarCommandToGlobalDir}" != "" ]]; then 
        
        # tar local folder to global dir  (name it like the host name $HOSTNAME or if not defined use $HOME)
        echo "$ES Tar ${Job:localDir}  --->  ${Job:globalDir} "
        cd ${Job:localDir}
        if [[ "${HOSTNAME}" == "" ]] ; then
            f="${HOME}-localOut.tar"
        else
            f="${HOSTNAME}-localOut.tar"
        fi
        ${Job:tarCommandToGlobalDir} "${Job:globalDir}/$f" -C "${Job:localDir}" ./
    else
        echo "$ES Copying ${Job:localDir}  --->  ${Job:globalDir} "
        cp -rP ${Job:localDir}/* ${Job:globalDir}/ 
    fi
    
    rm -rf ${Job:localDir}
fi

exit 0
