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
function ES(){ echo "$(currTime) :: process.sh: Rank: ${Job:processIdxVariabel}"; }

executionDir=$(pwd)

thisPID="$BASHPID"
signalReceived="False"
cleaningUp="False"

# save stdout in file descriptor 4
exec 4>&1



function trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}

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
function launchInForeground(){
  start=$(date +%s.%N) ;
  "$@"
  res=$?      
  end=$(date +%s.%N) ;
  printTime $start $end ;
  return $res  
}

function shutDownHandler() {
    # ignore all signals
    trap_with_arg ignoreAllSignals SIGINT SIGUSR1 SIGUSR2 SIGTERM SIGPIPE
    
    signalReceived="True"
    #if [[ "${cleaningUp}" == "False" ]]; then
      #echo "$(ES) Signal $1 catched, cleanup and exit."
      #cleanup
      #exitFunction 0
    #else
      #echo "$(ES) Signal $1 catched, we are already cleaning up, continue."
    #fi
    echo "$(ES) Signal $1 catched, exit..."
    exitFunction 0
}

function ignoreAllSignals(){
    echo "$(ES) already shutting down: ignoring signal: $1"
}

function exitFunction(){
    echo "Exiting $(ES) exit code: $1 (0=success)" 1>&4
    exit $1
}

yell() { echo "$0: $*" >&2; }
die() { yell "$1"; cleanup ; exitFunction 111 ; }
try() { "$@" || die "$(ES) cannot $*" ; }
dieNoCleanUp() { yell "$1"; exitFunction 111 ; }
tryNoCleanUp() { "$@" || die "$(ES) cannot $*" ;  }


# Setup the Trap
# Be aware that SIGINT and SIGTERM will be catched here, but if this script is run with mpirun
# mpirun will forward SIGINT/SIGTERM (wait a bit) and then quit, leaving this script still running in the signal handler
trap_with_arg shutDownHandler SIGINT SIGUSR1 SIGUSR2 SIGTERM SIGPIPE


tryNoCleanUp mkdir -p "${Job:processDir}"

logFile="${Job:processDir}/processLog.log"
echo "$(ES) make process log file at: ${logFile}"

#http://stackoverflow.com/a/18462920/293195
exec 3>&1 1>>${logFile} 2>&1

echo "$(ES) starting executable ..."
${Job:executableCommand}

exitFunction 0