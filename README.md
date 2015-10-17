# ClusterJobGenerator
Python module to generate highly configurable user-defined jobs on a high-performance cluster

If you are doing high performance computing on a linux cluster and are bored from dealing with tons of configurations files for maintaining a parallel job configuration.
This python module has been developed during research for granular rigid body dynamics where complex and huge parallel MPI jobs needed to be configured in an uniform an reproducable way by using mainly one configuration file which acts as the main config file for the jobs [Link](http://www.zfm.ethz.ch/~nuetzig/?page=research). These jobs uncluded parallel tasks such as visualization, e.g rendering, general rigid body simulations, data analysis and image correlation on the HPC Euler and Brutus at ETH Zürich.


This modules is best described with an example:
The user sets up a job configuration folder ``myJob`` consiting of two files ``Launch.ini`` and ``JobConfig.ini``.

  - **The ``Launch.ini``** is a config file for all command line arguments to the configurator script ``configureJob.py``. It is not so important but handy.
  - **The ``JobConfig.ini``** is **the main** job configuration file which is used for the job generator type specified at the command line to ``configureJob.py`` or in the ``Launch.ini``.

By using the ``configureJob.py`` script, the user configures the job (or a sequence of jobs) and the configuration files are written commonly to a job specific configuration folder
``myJob/Launch_myJob.0/`` (or ``myJob/Launch_myJob.0/``,``myJob/Launch_myJob.1/``,... for a sequence of job configurations). What configuration files are written is dependent on the generator type used. The job generator is specified in the ``Launch.ini``. The job generator is a python class which is loaded and executed. 

The main job generator for HPC tasks is the ``JobGeneratorMPI`` which generates a general launchable MPI task which consists of the following main Bash files:

  - **start.sh** : The start script which makes a global output folder (for example on a parallel filesystem) and
    asd
  - **preProcess.sh**
  - **process.sh**
  - **postProcess.sh**
  - **end.sh**

The configuration stage mainly consists of string substitutions (python format strings and special expressions) for template files which get written to the configuration folder mentioned above.
The ``JobConfig.ini`` file is used to define 

After the configuration of the job, the user can then submit the job to the batch system of the high-performance cluster.


