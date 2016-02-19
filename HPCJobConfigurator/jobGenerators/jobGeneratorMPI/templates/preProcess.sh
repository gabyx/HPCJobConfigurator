#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

function currTime(){ date +"%H:%M:%S.%3N"; }
function ES(){ echo "$(currTime) :: preProcess.sh: Rank: ${Job:processIdxVariabel}"; }


yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }


echo "$(ES) Remove and Make Directory:  ${Job:localDir}"
rm -r "${Job:localDir}" > /dev/null 2>&1
try mkdir -p "${Job:localDir}"

if [[ "${Job:copyLocation}" != "" ]]; then
    echo "$(ES) Create: temp folder" 
    try mkdir -p "${Job:localDir}/temp"
    echo "$(ES) Copy files to node"
    try cp -r "${Job:copyLocation}" "${Job:localDir}/temp/"
fi

exit 0
