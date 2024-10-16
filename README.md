# Splunk NSO Integration Example - Predictive Service Design
This repository provide a example of how to design a service based on Splunk Machine Learning(ML) prediction to prevent OOM scenrio. At the same time, obtain expectated time consumption before the service run. The goal is to make the service execution Predictive and provide a overview of what is going to happend before the server execution. 

# Dependency
* requests==2.28.2
* panda==2.2.3


# Requirment
* Python3.11 - Python3.12 might have competability issue. 
* Splunk
	* Splunk Enterprise
		* Local Install - https://www.splunk.com/en_us/download/splunk-enterprise.html
		* Splunk Docker Container - https://hub.docker.com/r/splunk/splunk/
	* Splunk Cloud - https://www.splunk.com/en_us/products/splunk-cloud-platform.html
    * Splunk Machine Learning Toolkit - https://splunkbase.splunk.com/app/2890

# Framwork Structure
```
.
├── README
├── load-dir
├── package-meta-data.xml
├── python
│   └── predictive_service
│       ├── __init__.py
│       ├── config
│       │   ├── splunk_config.json --> Splunk Configuration File
│       │   └── splunk_config.json.default --> Default Splunk Configuration File
│       ├── main.py  --> Main Service Logic
│       └── splunk_api.py --> Splunk REST API call to get ML data, process and take action
├── requirments.txt --> dependency
├── src
│   ├── Makefile
│   └── yang
│       └── predictive_service.yang --> Yang model for the service
├── templates
│   └── predictive_service-template.xml --> Create large order by user list
└── test
    ├── Makefile
    └── internal
        ├── Makefile
        └── lux
```

# Before Start
Install dependency
```
pip install -r requirments.txt
```


# Usage
1. Fill in the nessasary information in splunk_config.json.default 
    ```
    {
        "user": , --> Username for Splunk that allow to pull data
        "pass": , --> Password for the User that entered above
        "max_retry":, -->Max retry before the prediction is ready. For each retry will wait 5 second apart
        "splunk_ip":  --> Splunk IP and port in the following format "https://<splunk_ip>:<port>"
    }
    ```
2. Compile the service
    ```
    cd src; make clean all
    ```
3. Reload the service in NSO
    ```
    ncs_cli -C -u admin
    package reload
    ```
4. Run the service 
    ```
    admin@ncs(config)# predictive_service test2 max-length 50000
    admin@ncs(config-predictive_service-test2)# commit dry-run 
    ```
5. Observer th output in python VM log - ncs-python-vm-predictive_service.log


# What will this Service do
The service will not run and terminated with the following output
```
admin@ncs(config)# predictive_service test2 max-length 50000
admin@ncs(config-predictive_service-test2)# commit dry-run 
Aborted: Python cb_pre_modification error. Abort the service execution due to Potention OOM risk
```
Under the following scenrio
* If the data that extracted from the Splunk shows physical memory consumption(RSS) of the ncs.smp close to the 90% of the MemFree
* If the Commited_AS from Splunk will over the CommitLimit while overcommit_memory is 2

At the same tiem, the Python VM log will show the following
Request Splunk to Forecast and Fetching Memory Data (RSS)
```
<INFO> 12-Oct-2024::11:09:12.184 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - ***Start Splunk Forecasting***
<INFO> 12-Oct-2024::11:09:12.185 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Fetching memory data from Splunk
<INFO> 12-Oct-2024::11:09:12.185 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Contacting Splunk Datastore: https://10.147.40.101:8089
<INFO> 12-Oct-2024::11:09:12.277 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Creating job with sid: 1728724152.4814
```
Request Splunk to Forecast and Fetching Time Data
```
<INFO> 12-Oct-2024::11:09:22.575 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Creating job with sid: 1728724162.4815
<INFO> 12-Oct-2024::11:09:22.458 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Fetching time data from Splunk
<INFO> 12-Oct-2024::11:09:22.458 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Contacting Splunk Datastore: https://10.147.40.101:8089
```
Request Splunk to Forecast and Fetching Commited_AS Data
```
<INFO> 12-Oct-2024::11:09:32.758 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Fetching Commited_AS data from Splunk
<INFO> 12-Oct-2024::11:09:32.758 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Contacting Splunk Datastore: https://10.147.40.101:8089
<INFO> 12-Oct-2024::11:09:32.867 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Creating job with sid: 1728724172.4816
```

Process and proceed with action. Below shows a example of when Commited_AS might goes bigger than CommitLimit
```
<ERROR> 12-Oct-2024::11:09:43.60 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Commited_AS over CommitLimit
<INFO> 12-Oct-2024::11:09:43.60 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Expect time consumption 0:00:39.626565, RSS/Memory Limit: 261.93kb/14625824.4kb, Commited_AS/CommitLimit: 9972206.053970432/8143884, Recommended Action: Abort
<ERROR> 12-Oct-2024::11:09:43.60 predictive_service ncs-dp-3719214-predictive_service:main:0-1-th-60123: - Abort the service execution due to Potention OOM risk
Traceback (most recent call last):
  File "/home/leeli4/Tail-f-workenv/Tail-f-env/nso/nso_store/6.3.2/src/ncs/pyapi/ncs/application.py", line 875, in wrapper
    pl = fn(self, tctx, op, kp, root, proplist)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/leeli4/Tail-f-workenv/test/git/leeli4/splunk-example---predictive/nso/ncs-run/state/packages-in-use/1/predictive_service/python/predictive_service/main.py", line 46, in cb_pre_modification
    action=forecast(service.max_length, self.log)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/leeli4/Tail-f-workenv/test/git/leeli4/splunk-example---predictive/nso/ncs-run/state/packages-in-use/1/predictive_service/python/predictive_service/splunk_api.py", line 155, in forecast
    raise Exception(f'Abort the service execution due to Potention OOM risk')
Exception: Abort the service execution due to Potention OOM risk
```
Otherwise the service will proceed
```
<INFO> 12-Oct-2024::11:17:17.311 predictive_service ncs-dp-3729802-predictive_service:main:0-1-th-60144: - Evaluation will based on RSS. Ignore OOM Action due to overcommit_memory is: 0
<INFO> 12-Oct-2024::11:17:17.311 predictive_service ncs-dp-3729802-predictive_service:main:0-1-th-60144: - Expect time consumption 0:00:39.626565, RSS/Memory Limit: 261.93kb/14625824.4kb, Commited_AS/CommitLimit: 9972206.053970432/8143884, Recommended Action: Proceed
<INFO> 12-Oct-2024::11:17:17.314 predictive_service ncs-dp-3729802-predictive_service:main:0-1-th-60144: - Service create(service=/predictive_service:predictive_service{test2})
<INFO> 12-Oct-2024::11:17:17.315 predictive_service ncs-dp-3729802-predictive_service:main:0-1-th-60144: - Expected memory consumption not close to the critical limit. Proceed with service execution.
```



## Copyright and License Notice
``` 
Copyright (c) 2024 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
``` 
