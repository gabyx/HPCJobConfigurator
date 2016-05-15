# Job Configurator for Cluster Computing
## Python module to generate highly configurable user-defined jobs on a high-performance cluster

If you are doing high performance computing on a linux cluster and are bored from dealing with tons of configurations files for maintaining a parallel job configuration.
This python module has been developed during research for granular rigid body dynamics where complex and huge parallel MPI jobs needed to be configured in an uniform an reproducable way by using mainly one configuration file which acts as the main config file for the jobs [Link](http://www.zfm.ethz.ch/~nuetzig/?page=research). That included parallel tasks such as visualization, e.g rendering, general rigid body simulations, data analysis and image correlation on the HPC Euler and Brutus at ETH Zürich.

The absolut main advantage of this configurator is the ability to configure and test the job locally on your preferred workstation. The job can be fully launched locally and tested until everything is in place and works as expected and once this is the case it can be configured and submitted to the batch system on the cluster where it should complete sucessfully as well. (75% of the time :v:)

See the documentation on:
[Homepage](http://gabyx.github.io/HPCJobConfigurator)
