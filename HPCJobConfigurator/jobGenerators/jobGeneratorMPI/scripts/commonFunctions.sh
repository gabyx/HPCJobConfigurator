#!/bin/bash

# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

# Source this file in your bash script to use these functions
# The function ES() needs to be defines which is some script dependend string for debugging.

# Output the current time
function currTime(){ date +"%H:%M:%S.%3N"; }

# Simple exit function which needs a filedescriptor 4!
function exitFunction(){
    echo "Exiting $(ES) exit code: $1 (0=success), stage: ${stage}" 1>&4
    exit $1
}

# Some exception handling stuff
# You need to define a cleanup() function to make this work!
yell() { echo "$0: $*" >&2; }
die() { yell "$1"; cleanup ; exitFunction 111 ; }
try() { "$@" || die "$(ES) cannot $*" ; }
dieNoCleanUp() { yell "$1"; exitFunction 111 ; }
tryNoCleanUp() { "$@" || dieNoCleanUp "$(ES) cannot $*" ;  }

# Print the time
# Usage see launchInForeground
function printTime(){
    dt=$(echo "$2 - $1" | bc)
    dd=$(echo "$dt/86400" | bc)
    dt2=$(echo "$dt-86400*$dd" | bc)
    dh=$(echo "$dt2/3600" | bc)
    dt3=$(echo "$dt2-3600*$dh" | bc)
    dm=$(echo "$dt3/60" | bc)
    ds=$(echo "$dt3-60*$dm" | bc)
    printf "$(ES) Time Elapsed: %d:%02d:%02d:%02.4f\n" $dd $dh $dm $ds
}

# Launches any command given to this function in the foreground and times it.
function launchInForeground(){
  start=$(date +%s.%N) ;
  "$@"
  res=$?      
  end=$(date +%s.%N) ;
  printTime $start $end ;
  return $res  
}

# Trap setup function
# Usage: trap_with_arg shutDownHandler SIGINT SIGUSR1 SIGUSR2 SIGTERM SIGPIPE 
function trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}

# Simple handler to ignore the signal
function ignoreSignal(){
    echo "$(ES) already shutting down: ignoring signal: $1"
}
