
<img src="/images/logo-perf.jpg" alt="drawing" width="640" height="240"/>
<br />

# A toolchain for automated performance testing under Continous Integration
This project is being developed at CMS experiment at CERN for identifying performance issues during CI of python-based projects. This also includes [flask](https://flask.palletsprojects.com/en/1.1.x/) based web services running at CERN.
The toolchain is being used to analyze CERN CMS uploader service. See our [reproducible results](https://gitlab.cern.ch/omjaved/perfci-dataset).

# A quick grab

To quickly setup and run PerfCI, we provide scripts to automate PerfCI performance testing on a project. This can be found in this [link](https://gitlab.cern.ch/omjaved/perfci-example-runner)


# Toolchain stages
The flow diagram shows different stages of the toolchain. We can see how the toolchain leverages existing CI setup and unit tests for performance testing.

<img src="/images/flow.jpg" alt="drawing" width="320" height="200"/>
<br />

## Stage 1 Specifying performance testing tasks

This repository consists of source code and documentation for Stage 1 of the toolchain i.e., it allows users to provide performance testing tasks in a configuration file.

### Tutorial on how to specify performance tasks

Refer to our [wiki](https://gitlab.cern.ch/omjaved/perfci/-/wikis/Tutorial-for-running-automated-performance-testing-during-Continuous-Integration-(PERFCI)) page


## Stage 2 of the toolchain uses runtime verification to monitor unit tests during CI.

Source code of Runtime Verification framework extended for CI can be found in [CI-VYPR](https://github.com/JesperStromblad/VyPR), [VyPR server](https://github.com/JesperStromblad/VyPRServer) and its [documentation](http://vypr.web.cern.ch/vypr/use-vypr.html)

Specification is written in a language called PyCFTL specification.
See [paper](https://link.springer.com/chapter/10.1007/978-3-030-32079-9_12)


## Stage 3 of the toolchain analyzes performance data during CI
Source code of [Analysis Library](https://github.com/pyvypr/VyPRAnalysis) and its [documentation](http://vypr.web.cern.ch/vypr/analysis-docs/)


# Short video demonstration

You can also see our  youtube video to follow the demonstration of our toolchain easily. Please also see the description box of the video.

[![](http://img.youtube.com/vi/RDmXMKA1v7g/0.jpg)](http://www.youtube.com/watch?v=RDmXMKA1v7g "PerfCI")


## Getting Started

These instructions will get you a copy of the project up and running on your local machine. Please refer to documentation before getting started.

### Prerequisites


```
pip install -r requirements.txt
```

### Running automated performance testing

Create a directory 'perfdata' into the root of your project. Put the `vypr.config` file from the perfci to perfdata directory.


### Extended Performance CI file

Create our performance config file '.perf-ci.yml'. This is placed in the root directory of the project along with the original CI file e.g., .gitlab-ci.yml.
Avoid specifying plugin and specification in the same CI process. This may cause instrumentation interference. See our configuration file in `sample/` directory.

Following is the example of our performance CI configuration file which shows all the available tasks.

```
performance:

  input-collection: |
     from cunit.base_test_class import BaseTestClass
     import os
     input_list = [1,2,3,4,5,6,7,8,9,10]
     for input in input_list:
         BaseTestClass.dicover_test_path(os.getcwd()+'/test')
         BaseTestClass.test_case_loader(input,False,input)

  NOTE: you can also provide a path to the python file shown as follows:

  input-collection:
    - script-path: '/path/anyname.py'

  fail-fast: True

  unit-test-measurement:
    - plugin: UnitTestTimeMeasurement

  check-point:
    - resume: 5
    - stop: 8

  performance-specification:
    - '/absolute_path/VyPR_queries.py'
```


## Authors

* **Omar Javed**

See also the list of [contributors](https://gitlab.com/your/project/contributors) who participated in this project.









