# Folding@Home Docker on Mesos

![DockerHub Pulls](https://badgen.net/docker/pulls/yurinnick/folding-at-home?icon=docker)
![DockerHub Stars](https://badgen.net/docker/stars/yurinnick/folding-at-home?icon=star&label=stars)

Folding@home is a project focused on disease research. The problems we’re solving
require so many computer calcul­ations – and we need your help to find the cures!

## Image Flavors

Currently there are two types of image available:
- `latest`, `cpu` - lightweight image for CPU only workloads


## Mesos: Usage

#### Run agent in oversubscribed mode in CPU.

Copy the mesos-agent.service to the appropiate path. This example use `Fixed` Resource Estimator and `Load` QoS Controller by default. These parameters are added in mesos-agent daemon to make resources oversubscribed in the agent:

```
--resource_estimator="org_apache_mesos_FixedResourceEstimator"
--qos_controller="org_apache_mesos_LoadQoSController" 
--oversubscribed_resources_interval=15secs 
--qos_correction_interval_min="20secs" 
--modules=file:///path/to/modules.json"
```

#### Run the framework with revocable resources

The docker image is downloaded from repo `aidaph/folding-at-home:latest`. To run the framework:

```
python framework.py "zk://IPMESOSMASTER:2181/mesos"
```


```
docker run \
  --name folding-at-home \
  -p 7396:7396 \
  -p 36330:36330 \
  -e USER=Anonymous \
  -e TEAM=0 \
  -e ENABLE_GPU=[true|false] \
  -e ENABLE_SMP=true \
  --restart unless-stopped \
  yurinnick/folding-at-home:[latest|latest-nvidia]
```
