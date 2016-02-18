#!/bin/bash
# =====================================================================
#  HPCJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================


ES="launch.sh:"

# Trick the batch system to see this script as an MPI
# the commands below with /usr/bin/time
mpirun --version > /dev/null 2>&1

thisPID="$BASHPID"

stage=0
signalReceived="False"
cleaningUp="False"

function exitFunction(){
    
    echo "Exiting $ES exit code: $1 (0=success), stage: ${stage}"
    if [[ ${signalReceived} == "True" ]]; then
      # http://www.cons.org/cracauer/sigint.html
      # kill ourself to signal calling process that we exited on signal
      trap - SIGINT
      kill -s SIGINT ${thisPID}
    else
      exit $1
    fi
}

function trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}


function cleanup(){
    
    if [[ ${cleaningUp} == "True" ]] ; then
        # we are already cleaning up
        return 0
    else
        cleaningUp="True"
    fi
    
    echo "$ES Script in stage $stage!"
    if [[ $stage -ge 2 ]]; then
        # Postprocess per node
        echo "$ES Execute Postprocess =================="
          stage=3
          launchInForeground mpirun -npernode 1 ${TemplatesOut:postProcessPerNode}
        echo "$ES ======================================"

        echo "$ES Execute End =========================="
          stage=4
          launchInForeground ${TemplatesOut:endJob}
        echo "$ES ======================================"
    else
        # launch did not reach at least stage 2 (process)
        # clean up everything
        echo "$ES cleanup: Standard clean up... (delete local dir) ====="
          launchInForeground mpirun -npernode 1 rm -rf ${Job:localDir}  
        echo "$ES cleanup: ============================================="
    fi
}

function ignoreAllSignals(){
    echo "$ES already shutting down: ignoring signal: $1"
}
function shutDownHandler() {
    # make ignoring all signals
    trap_with_arg ignoreAllSignals SIGINT SIGTERM SIGUSR1 SIGUSR2 

    signalReceived="True"
    
    if [[ ${cleaningUp} == "False" ]]; then
      echo "$ES Signal $1 catched, cleanup and exit."
      cleanup
      exitFunction 0
    else
      echo "$ES Signal $1 catched, we are already cleaning up, continue."
    fi
}

function printTime(){
    dt=$(echo "$2 - $1" | bc)
    dd=$(echo "$dt/86400" | bc)
    dt2=$(echo "$dt-86400*$dd" | bc)
    dh=$(echo "$dt2/3600" | bc)
    dt3=$(echo "$dt2-3600*$dh" | bc)
    dm=$(echo "$dt3/60" | bc)
    ds=$(echo "$dt3-60*$dm" | bc)
    printf "$ES Time Elapsed: %d:%02d:%02d:%02.4f\n" $dd $dh $dm $ds
}

function launchInForeground(){
  start=$(date +%s.%N) ;
  "$@"
  res=$?      
  end=$(date +%s.%N) ;
  printTime $start $end ;
  return $res  
}

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; cleanup ; exitFunction 111; }
try() { "$@" || die "$ES cannot $*"; }


# Setup the Trap
trap_with_arg shutDownHandler SIGINT SIGTERM SIGUSR1 SIGUSR2 

echo "$ES Execute Start ========================"
# stage which indicates in which state the program was, 0= nothing executed, 1=proprocess executed, 2=launch executed, 3= post executed
stage=0
  try launchInForeground ${TemplatesOut:startJob}
echo "$ES ======================================"


# Preprocess per node
echo "$ES Execute Preprocess ==================="
stage=1
  try launchInForeground mpirun -npernode 1 ${TemplatesOut:preProcessPerNode}
echo "$ES ======================================"


# Run processes
echo "$ES Run MPI Task ========================="
stage=2
  try launchInForeground mpirun -np ${Cluster:nProcesses} ${TemplatesOut:processPerCore}
echo "$ES ======================================"

# Run cleanup
cleanup

exitFunction 0