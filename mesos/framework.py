import logging
import uuid
import os
import sys
import time

from mesos.interface import Scheduler, mesos_pb2
from mesos.scheduler import MesosSchedulerDriver

logging.basicConfig(level=logging.INFO)

TASK_CPUS = 1
TASK_MEM = 128

class MyScheduler(Scheduler):

    def registered(self, driver, framework_id, master_info):
        logging.info("Registered with frameworkd id: %s on: %s", 
                      framework_id, master_info.hostname)


    def resourceOffers(self, driver, offers):
        logging.info("Received resource offers: %s",
                    [o.id.value for o in offers])
        for offer in offers:
            #task = new_task(offer)
            task = mesos_pb2.TaskInfo()
            task.task_id.value  = str(uuid.uuid4())
            task.slave_id.value = offer.slave_id.value
            task.name           = "MyTask"
            # task.executor.MergeFrom(self.executor)
            # task.command = # By default it is "docker run image" 
            
            containerinfo = mesos_pb2.ContainerInfo()
            containerinfo.type = containerinfo.DOCKER

            dockerinfo = containerinfo.DockerInfo()
            dockerinfo.image = "aidaph/folding-at-home:latest"
            dockerinfo.force_pull_image = True
            containerinfo.docker.CopyFrom(dockerinfo)
            
            commandinfo = mesos_pb2.CommandInfo()
            commandinfo.value = "/opt/fahclient/FAHClient --user='XXX' --team='XXX' --passkey='XXXX' "

            task.container.CopyFrom(containerinfo)
            task.command.CopyFrom(commandinfo)

            cpus = task.resources.add()
            cpus.name = "cpus"
            cpus.type = mesos_pb2.Value.SCALAR
            cpus.scalar.value = TASK_CPUS

            mem = task.resources.add()
            mem.name = "mem"
            mem.type = mesos_pb2.Value.SCALAR
            mem.scalar.value = TASK_MEM

            #task.command.value = "while [ true ]; do echo hello; done"
            time.sleep(5)
            logging.info("Launching task %s"
                         "using offer %s.",
                         task.task_id.value,
                         offer.id.value)
            # Frameworks can choose to launch tasks on revocable resources by using the regular launchTasks() API.
            driver.launchTasks(offer.id, [task])


    def statusUpdate(self,driver,update):
       '''
       when a task is started, over, killed or lost (slave crash, ...), this method
       will be triggered with a status message.
       '''
       logging.info("Task %s is in state %s" %
                   (update.task_id.value,
                    mesos_pb2.TaskState.Name(update.state)))


    def new_task(self,offer):
        task = mesos_pb2.TaskInfo()
        task.task_id.value  = str(uuid.uuid4())
        task.slave_id.value = offer.slave_id.value
        task.name           = "MyTask"

        cpus = task.resources.add()
        cpus.name = "cpus"
        cpus.type = mesos_pb2.Value.SCALAR
        cpus.scalar.value = TASK_CPUS

        mem = task.resources.add()
        mem.name = "mem"
        mem.type = mesos_pb2.Value.SCALAR
        mem.scalar.value = TASK_MEM

        return task

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s master" % sys.argv[0]
        sys.exit(1)
    
    framework       = mesos_pb2.FrameworkInfo()
    framework.user  = "" # Have Mesos fill in the current user.
    framework.name  = "MyFramework"
    ### Add the REVOCABLE_RESOURCES capability to framework
    capability      = framework.Capability()
    capability.type = framework.Capability.REVOCABLE_RESOURCES
    framework.capabilities.append(capability)

    driver = MesosSchedulerDriver(
            MyScheduler(), 
            framework,
            sys.argv[1]
            )
    driver.run()
