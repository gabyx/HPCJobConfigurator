# =====================================================================
#  HPClusterJobConfigurator
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

timeCmd=$(which time)

function exitFunction(){
    echo "Exiting launch.sh, exit code: $1 (0=success)!"
    exit $1
}

function trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}


function cleanup(){
    
    echo "$ES Script in stage $stage!"
    
    if [[ $stage -eq 2 ]]; then
        stage=3
    elif [[ $stage -eq 3 ]]; then
        stage=4
    elif [[ $stage -eq 4 ]]; then
        stage=5
    else
        # launch did not reach at least stage 2 (process)
        # clean up everything
        stage=111
    fi
    
    if [[ $stage -eq 3 ]]; then
        echo "$ES cleanup: Execute post-process ========================"
        $timeCmd -f"\n$ES Time Elapsed: %E" mpirun -npernode 1 ${TemplatesOut:postProcessPerNode}
        echo "$ES cleanup: ============================================="
        stage=4 # move to stage 4
    fi
    
    if [[ $stage -eq 4 ]]; then
        echo "$ES cleanup: Execute end ================================="
        $timeCmd -f"\n$ES Time Elapsed: %E" ${TemplatesOut:endJob}
        echo "$ES cleanup: ============================================="
    fi
    
    # cleanup everything
    if [[ $stage -eq 111 ]]; then
        echo "$ES cleanup: Standard clean up... (delete local dir) ====="
        $timeCmd -f"\n$ES Time Elapsed: %E" mpirun -npernode 1 rm -rf ${Job:localDir}  
        echo "$ES cleanup: ============================================="
    fi
    
}

function signalHandler() {
    echo "$ES Signal $1 catched, cleanup and exit."
    cleanup
    exitFunction 0
}

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; cleanup ; exit 111 ; }
try() { "$@" || die "$ES cannot $*"; }



# Setup the Trap
trap_with_arg signalHandler SIGINT SIGTERM SIGUSR1 SIGUSR2 

echo "$ES Execute Start ========================"
# stage which indicates in which state the program was, 0= nothing executed, 1=proprocess executed, 2=launch executed, 3= post executed
stage=0
try $timeCmd -f"\n$ES Time Elapsed: %E" ${TemplatesOut:startJob}
echo "$ES ======================================"


# Preprocess per node, make a directory to store simulation data
echo "$ES Execute Preprocess ==================="
stage=1
try $timeCmd -f"\n$ES Time Elapsed: %E" mpirun -npernode 1 ${TemplatesOut:preProcessPerNode}
echo "$ES ======================================"


# Run simulation
echo "$ES Run MPI Task ========================="
stage=2
try $timeCmd -f"\n$ES Time Elapsed: %E" mpirun -np ${Cluster:nProcesses} ${TemplatesOut:processPerCore} 
echo "$ES ======================================"

#Postprocess per node, move the directory to the work scratch
echo "$ES Execute Postprocess =================="
stage=3
try $timeCmd -f"\n$ES Time Elapsed: %E" mpirun -npernode 1 ${TemplatesOut:postProcessPerNode} 
echo "$ES ======================================"

echo "$ES Execute End =========================="
stage=4
try time -f"\n$ES Time Elapsed: %E" ${TemplatesOut:endJob}
echo "$ES ======================================"

exitFunction 0