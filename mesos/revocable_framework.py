import logging
import uuid
import os
import sys
import time

from mesos.interface import Scheduler, mesos_pb2
from mesos.scheduler import MesosSchedulerDriver

logging.basicConfig(level=logging.INFO)

TOTAL_TASKS = 1

TASK_CPUS = 8
TASK_MEM = 12000

class MyScheduler(Scheduler):

    def __init__(self):
        self.tasksLaunched = 0
        self.tasksFinished  = 0


    def registered(self, driver, framework_id, master_info):
        logging.info("Registered with frameworkd id: %s on: %s", 
                      framework_id, master_info.hostname)


    def resourceOffers(self, driver, offers):
        logging.info("Received resource offers: %s",
                    [o.id.value for o in offers])
        for offer in offers:
            tasks = []
            remainCpus = 0
            remainMem = 0
            for resource in offer.resources:
                if resource.name == "cpus":
                    remainCpus = resource.scalar.value
                elif resource.name == "mem":
                    remainMem  = resource.scalar.value


#            print ("### 1. remainingCpus", remainingCpus)
            #maxTasks = self.maxTasksForOffer(offer)
            #print "maxTasksForOffer: [%d]" % maxTasks   
            
            while self.tasksLaunched < TOTAL_TASKS and \
                  remainCpus >= TASK_CPUS and \
                  remainMem >= TASK_MEM:
            #for i in range(maxTasks / 2):
                tid = self.tasksLaunched
                self.tasksLaunched += 1

                print "Launching task %d using offer %s" \
                      % (tid, offer.id.value)

                task = mesos_pb2.TaskInfo()
                task.task_id.value  = str(uuid.uuid4())
                task.slave_id.value = offer.slave_id.value
                task.name           = "fah"
                # task.executor.MergeFrom(self.executor)
                # task.command.value = "sleep 1000" # By default it is "docker run image" 
            
                containerinfo = mesos_pb2.ContainerInfo()
                containerinfo.type = containerinfo.DOCKER

                dockerinfo = containerinfo.DockerInfo()
                dockerinfo.image = "aidaph/folding-at-home:latest"
                dockerinfo.force_pull_image = True
                containerinfo.docker.CopyFrom(dockerinfo)
            
                commandinfo = mesos_pb2.CommandInfo()
                commandinfo.value = "/opt/fahclient/FAHClient --power=medium --user='XXX' --team='XXX' --passkey='XXX' "

                task.container.CopyFrom(containerinfo)
                task.command.CopyFrom(commandinfo)

                cpus = task.resources.add()
                cpus.name = "cpus"
                cpus.type = mesos_pb2.Value.SCALAR
                cpus.scalar.value = TASK_CPUS
                cpus.revocable.MergeFrom(cpus.RevocableInfo())

                mem = task.resources.add()
                mem.name = "mem"
                mem.type = mesos_pb2.Value.SCALAR
                mem.scalar.value = TASK_MEM
                mem.revocable.MergeFrom(mem.RevocableInfo())

                tasks.append(task)

                remainCpus -= TASK_CPUS
                remainMem -= TASK_MEM

            if tasks:
                print "Accepting offer on [%s]" % offer.hostname
                driver.launchTasks(offer.id, tasks)
            else:
                print "Declining offer on [%s]" % offer.hostname
                driver.declineOffer(offer.id)

            time.sleep(5)
#            logging.info("Launching task %s"
#                         "using offer %s.",
#                         task.task_id.value,
#                         offer.id.value)
            # Frameworks can choose to launch tasks on revocable resources by using the regular launchTasks() API.
            #driver.launchTasks(offer.id, [task])
#            operation = mesos_pb2.Offer.Operation()
#            operation.type = mesos_pb2.Offer.Operation.LAUNCH
#            operation.launch.task_infos.extend(tasks)
#
#            driver.acceptOffers([offer.id], [operation])

    def statusUpdate(self,driver,update):
       '''
       when a task is started, over, killed or lost (slave crash, ...), this method
       will be triggered with a status message.
       '''
       logging.info("Task %s is in state %s" %
                   (update.task_id.value,
                    mesos_pb2.TaskState.Name(update.state)))

       if update.state == mesos_pb2.TASK_FINISHED:  # Running
           self.tasksFinished += 1
           
       if self.tasksFinished == TOTAL_TASKS:  
           driver.stop()
       

     #  if update.state == mesos_pb2.TASK_LOST or \
     #     update.state == mesos_pb2.TASK_KILLED or \
     #     update.state == mesos_pb2.TASK_FAILED or \
     #     update.state == mesos_pb2.TASK_ERROR:
     #      print "Aborting because task %s is in unexpected state %s with message '%s'" \
     #           % (update.task_id.value, mesos_pb2.TaskState.Name(update.state), update.message)
     #      driver.abort()

    def maxTasksForOffer(self, offer):
        count = 0
        cpus = next(rsc.scalar.value for rsc in offer.resources if rsc.name == "cpus")
        mem = next(rsc.scalar.value for rsc in offer.resources if rsc.name == "mem")
        while cpus >= TASK_CPUS and mem >= TASK_MEM:
            count += 1
            cpus -= TASK_CPUS
            mem -= TASK_MEM
        return count


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

    status = 0 if driver.run() == mesos_pb2.DRIVER_STOPPED else 1

    # Ensure that the driver process terminates.
    driver.stop();

    sys.exit(status)
