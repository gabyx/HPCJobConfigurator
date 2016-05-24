# Job Configurator for Cluster Computing

![Build Status](https://travis-ci.org/gabyx/HPCJobConfigurator.svg?branch=master)

## Python module to generate highly configurable user-defined jobs on a high-performance cluster

If you are doing high performance computing on a linux cluster and are bored from dealing with tons of configurations files for maintaining a parallel job configuration.
This python module has been developed during research for granular rigid body dynamics where complex and huge parallel MPI jobs needed to be configured in an uniform an reproducible way by using one single main config file for the [jobs](http://http://gabyx.github.io/GRSFramework/#videos). That included parallel tasks such as 3d rendering, general rigid body simulations, data analysis and image correlation on the HPC Euler and Brutus at ETH Zürich.

The absolute main advantage of this configurator is the ability to configure and test the job locally on your preferred workstation. The job can be fully launched locally and tested until everything is in place and works as expected. Then, the job can be configured on a remote cluster and submitted to the batch system where it should complete successfully as well. (75% of the time :-)

See the documentation on:
[Homepage](http://gabyx.github.io/HPCJobConfigurator)
