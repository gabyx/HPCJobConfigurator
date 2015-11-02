# HPC Cluster Job Configurator
Python module to generate highly configurable user-defined jobs on a high-performance cluster

If you are doing high performance computing on a linux cluster and are bored from dealing with tons of configurations files for maintaining a parallel job configuration.
This python module has been developed during research for granular rigid body dynamics where complex and huge parallel MPI jobs needed to be configured in an uniform an reproducable way by using mainly one configuration file which acts as the main config file for the jobs [Link](http://www.zfm.ethz.ch/~nuetzig/?page=research). That included parallel tasks such as visualization, e.g rendering, general rigid body simulations, data analysis and image correlation on the HPC Euler and Brutus at ETH Zürich.

The absolut main advantage of this configurator is the ability to configure and test the job locally on your preferred workstation. The job can be fully launched locally and tested until everything is in place and works as expected and once this is the case it can be configured and submitted to the batch system on the cluster where it should complete sucessfully as well. (75% of the time :v:)


This module is best described with an example:
The user sets up a job configuration folder ``myJob`` consiting of two files ``Launch.ini`` and ``JobConfig.ini``.

  - **The ``Launch.ini``** is a config file for all command line arguments to the configurator script ``configureJob.py``. It is not so important but handy.
  - **The ``JobConfig.ini``** is **the main** job configuration file which is used for the job generator type specified at the command line to ``configureJob.py`` or in the ``Launch.ini``.

By using the ``configureJob.py`` script, the user configures the job (or a sequence of jobs) and the configuration files are written commonly to a job specific configuration folder
``myJob/Launch_myJob.0/`` (or ``myJob/Launch_myJob.0/``,``myJob/Launch_myJob.1/``,... for a sequence of job configurations). What configuration files are written is dependent on the used type of job generator. The job generator is specified in the ``Launch.ini``. The job generator is a python class which is loaded and executed. 

The main job generator for HPC tasks is the ``JobGeneratorMPI`` which generates a general launchable MPI task which consists of the following main Bash files executed in the main execution file ``launch.sh`` :

  - **start.sh** : The start script which makes a global output folder (for example on a parallel filesystem) and sends an email to the user to inform him that the job has been started
  - **preProcess.sh** The pre-process script is executed for each node on the cluser (by using ``mpirun`` in ``launch.sh``). This pre-process is responsible to setup node specific scratch folders and other stuff, such as copying files to the node locally etc.
  - **process.sh** The main process which is executed for each process on the HPC (by using ``mpirun`` in ``launch.sh``)
  - **postProcess.sh** The post-process which does file copies and clean up stuff and runs once for each single node (by using ``mpirun`` in ``launch.sh``).
  - **end.sh** The overall final process which at the end send the user an email that the job has finished.

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
All ``${section:option}`` strings (template strings) are replaced by the specified values in ``Launch.ini`` and especially ``JobConfig.ini``. Let us look at some extraction of these files:

**Launch.ini :**  
```
...
[Cluster]
jobName = MyDataVisualization-Test1
mailAddress = user@mail.com
...
```
**JobConfig.ini :**
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
myOtherFancyTemplate    = ./path/to/some/template.xml

myOtherFancyTemplate2   = { "inputFile" : "${MyStuff:file}" , "configurator" : { "modulePath" : "${General:modulePathGenerators}/jobGenerators/dictionaryAdjuster.py" , "moduleName" : "dictionaryAdjuster" , "className" : "DictionaryAdjuster" }, "settings" : {"additionalFiles" : [{"path":"${General:currentWorkDir}/data/ExperimentSettings.json" , "parentName":"expSettings"}] } }

[TemplatesOut]
myOtherFancyTemplate2   = ${Job:scriptDir}/config.xml

[MyStuff]
file = "${General:currentWorkDir}/../configIN.xml"

...
```
As can be seen, the variables in both ``.ini`` files are interpolated, and can be used all over the place.
Also environment variables are possible, specified by the syntax ``ENV::Variable``.
The user is free to add arbitrary variable definitions and use those in other templates (any text file) for example the ``myOtherFancyTemplate`` or ``myOtherFancyTemplate2`` above.
The job generator uses ``.ini`` files because they allow comments and explanations which is pleasing. (This will be changed to ``.json`` or ``.json`` files in the future)
The options under the ``Template`` section specifies the template files to be substituted, if no same option is present under the ``TemplateOut`` section which specifies the output file, the files are written to the folder ``${Job:scriptDir}``
The ``myOtherFancyTemplate2`` is a template where the string in ``{...}`` is parsed as JSON string and allows the user to specify a special template adjuster. The default one is the one given above, namely the ``DictionaryAdjuster`` in ``jobGenerators/dictionaryAdjuster.py`` which can be given a set of other ``"additionalFiles"`` (JSON files) which are parsed and added to the set of replacement variables. This means the ``file`` under the section ``MyStuff`` can contain dictionary references, e.g. ``${expSettings:A:B:dimension}``, given in the json file ``${General:currentWorkDir}/data/ExperimentSettings.json``:

**ExperimentSettings.json**
```
{
  "A" : { 
          "B": {
          "dimension" : [1,2,3] , "width" : 10 
          }
        }  
}
```

To be continued...

