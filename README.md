# Job Configurator for Cluster Computing 
## Python module to generate highly configurable user-defined jobs on a high-performance cluster

If you are doing high performance computing on a linux cluster and are bored from dealing with tons of configurations files for maintaining a parallel job configuration.
This python module has been developed during research for granular rigid body dynamics where complex and huge parallel MPI jobs needed to be configured in an uniform an reproducable way by using mainly one configuration file which acts as the main config file for the jobs [Link](http://www.zfm.ethz.ch/~nuetzig/?page=research). That included parallel tasks such as visualization, e.g rendering, general rigid body simulations, data analysis and image correlation on the HPC Euler and Brutus at ETH Zürich.

The absolut main advantage of this configurator is the ability to configure and test the job locally on your preferred workstation. The job can be fully launched locally and tested until everything is in place and works as expected and once this is the case it can be configured and submitted to the batch system on the cluster where it should complete sucessfully as well. (75% of the time :v:)

This module is best described with an example:
## General Workflow
The user sets up a job configuration folder ``myJob`` consiting of two files ``Launch.ini`` and ``JobConfig.ini``.

  - **The ``Launch.ini``** is a config file for all command line arguments to the configurator script ``configureJob.py``. It is not so important but handy.
  - **The ``JobConfig.ini``** is **the main** job configuration file which is used for the job generator type specified at the command line to ``configureJob.py`` or in the ``Launch.ini``.

By using the ``configureJob.py`` script, the user configures the job (or a sequence of jobs) and the configuration files are written commonly to a job specific configuration folder
``myJob/Launch_myJob.0/`` (or ``myJob/Launch_myJob.0/``,``myJob/Launch_myJob.1/``,... for a sequence of job configurations). What configuration files are written is dependent on the used type of job generator. The job generator is specified in the ``Launch.ini``.  **The job generator is a python class which is loaded and executed.** 

### The JobGeneratatorMPI
The main job generator for HPC tasks is the ``JobGeneratorMPI`` which generates a general launchable MPI task which consists of the following main Bash files executed in the main execution file ``launch.sh`` :

  - **[start.sh](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/HPCJobConfigurator/jobGenerators/jobGeneratorMPI/templates/start.sh)** : The start script which makes a global output folder (for example on a parallel filesystem) and sends an email to the user to inform him that the job has been started
  - **[preProcess.sh](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/HPCJobConfigurator/jobGenerators/jobGeneratorMPI/templates/preProcess.sh)** The pre-process script is executed for each node on the cluser (by using ``mpirun`` in ``launch.sh``). This pre-process is responsible to setup node specific scratch folders and other stuff, such as copying files to the node locally etc.
  - **[process.sh](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/HPCJobConfigurator/jobGenerators/jobGeneratorMPI/templates/process.sh)** The main process which is executed for each process on the HPC (by using ``mpirun`` in ``launch.sh``)
  - **[postProcess.sh](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/HPCJobConfigurator/jobGenerators/jobGeneratorMPI/templates/postProcess.sh)** The post-process which does file copies and clean up stuff and runs once for each single node (by using ``mpirun`` in ``launch.sh``).
  - **[end.sh](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/jobGenerators/jobGeneratorMPI/templates/end.sh)** The overall final process which at the end send the user an email that the job has finished.

All these files can be adapted to the user need!
Lets look for example at the template ``start.sh``:

```
#!/bin/bash    
ES="start.sh:"

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 1 ; }
try() { "$@" || die "cannot $*"; }

if [[ "${Cluster:mailAddress}" != "" ]];  then
    echo "EOM" | mail -s "Job: ${Job:jobName} has started" ${Cluster:mailAddress} 
fi

#echo "Make global dir ${Job:globalDir}" 
try mkdir -p ${Job:globalDir} 

exit 0
```
All ``${section:option}`` strings (template strings) are replaced by the specified values in ``Launch.ini`` and especially ``JobConfig.ini``. 

The [simple](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/example/simple/) example job which has the following folder structure
```
├── JobConfig.ini                # Job configuration .ini file 
├── Launch.ini                   # configureJob.py .ini file
├── data
│   └── DataVisSettings.json     # some data to be used to configure the tempaltes
├── scripts
│   └── simpleExeConfigurator.py # the configurator
└── templates                    # two template files which are configured
    ├── Input1.xml
    └── Input2.txt
````
The [simple](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/example/simple/) example job can be configured by
```
cd examples/simple
export MYGLOBALSCRATCH_DIR="$(pwd)/scratch/global"
export MYLOCALSCRATCH_DIR="$(pwd)/scratch/local"
python3 ../../HPCJobConfigurator/configureJob.py -x JobConfig.ini 
```
which configures one job under ``examples/simple/cluster/Launch_MyDataVisualization.0``.

Lets look at some extraction of the two .ini files above:

**[Launch.ini](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/example/simple/Launch.ini):**  
```
...
[Cluster]
jobName = MyDataVisualization
mailAddress = user@mail.com
...
```
**[JobConfig.ini](https://github.com/gabyx/HPClusterJobConfigurator/blob/master/example/simple/JobConfig.ini):**
```
...
[Job]
globalDir            = ENV::MYGLOBALSCRATCH_DIR/${Cluster:jobName}/${Cluster:jobName}.${Job:jobIdx}
localDir             = ENV::MYLOCALSCRATCH_DIR/${Cluster:jobName}.${Job:jobIdx}

jobName              = ${Cluster:jobName}.${Job:jobIdx}
scriptDirName        = Launch_${Job:jobName}
scriptDir            = ${Cluster:jobGeneratorOutputDir}/${Job:scriptDirName}


[Templates]
startJob                = ${General:modulePathGenerators}/jobGenerators/jobGeneratorMPI/generatorToolPipeline/templates/start.sh
# ....

# other templates ...... 
myOtherFancyTemplate    = ${General:jobDir}/templates/input1.xml
myOtherFancyTemplate2   = { "inputFile" : "${General:jobDir}/templates/input2.txt" , "configurator" : { "modulePath" : "${General:modulePathConfigurator}/jobGenerators/dictionaryAdjuster.py" , "moduleName" : "dictionaryAdjuster" , "className" : "DictionaryAdjuster" }, "settings" : {"additionalFiles" : [{"path":"${General:jobDir}/data/DataVisSettings.json" , "parentName":"gaga2"}] } }

[TemplatesOut]
myOtherFancyTemplate2   = ${Job:scriptDir}/input2.txt

[MySettings]

exeCommand = echo "Input1: " ; cat ${TemplatesOut:myOtherFancyTemplate}; echo "Input2: " ; cat ${TemplatesOut:myOtherFancyTemplate2} ;

dataType = grid
...
```
As can be seen, the variables (in the form ``${section:option}``) in both ``.ini`` files are interpolated, and can be used all over the place.
Also environment variables are possible, specified by the syntax ``ENV::Variable``.

The user is free to add arbitrary variable definitions and use those in other templates (any text based files such as ``.xml,.txt,.json`` etc.) for example the ``myOtherFancyTemplate`` or ``myOtherFancyTemplate2`` above.
The job generator uses ``.ini`` files because they allow comments and explanations which is pleasing. (That might possible change in the future to support also ``.json`` files)
The options under the ``Template`` section specifies the template files to be substituted, if no same option is present under the ``TemplateOut`` section which specifies the output file, the files are written to the folder ``${Job:scriptDir}``

The ``myOtherFancyTemplate2`` is a template where the string in ``{...}`` is parsed as JSON string and allows the user to specify a special template adjuster (substituter). The default one is the one given above, namely the ``DictionaryAdjuster`` in ``jobGenerators/dictionaryAdjuster.py`` which can be given a set of other ``"additionalFiles"`` (JSON files) which are parsed and added to the set of replacement strings. This means the ``${General:jobDir}/templates/input2.txt`` under the section can contain dictionary references, e.g. ``${gaga2:dic1:dic2:dic3:value}``, given in the json file ``${General:jobDir}/data/DataVisSettings.json`` and also references to variables in the ``.ini`` files.

If you look at the output folder ``examples/simple/cluster/Launch_MyDataVisualization.0``, you will find all configured scripts, bash scripts to launch the MPI job and so on.



Of course this is only a simple example. A more difficult example is provided by a an Image Correlation Task where each MPI process executes a tool pipeline consisting of some image processing and afterwards some image correlation, this job is explained in the following to give the user more insight how this tool works and how it can be extendet.

## Parallel Image Coorelation Job 
to be continued


## JobGeneratorMPI
  
  Important stuff to be documented:
  - localDir might only become a valid absolut path if fully expanded by Bash on a cluster (might contain Job specific variable such as $TMPDIR )
    therefore do not store this value in configuration files which are not Bash scripts! If you need localDir hand it to your executable and deal with it.
    

## Dependencies
python 3, lxml, glob2, jsonpickle, demjson, AttrMap
