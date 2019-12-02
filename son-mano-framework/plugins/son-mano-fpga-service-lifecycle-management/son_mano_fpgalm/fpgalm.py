"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.
This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""

import logging
import uuid
import requests
import yaml
import time
import os
import json
import concurrent.futures as pool

from sonmanobase.plugin import ManoBasePlugin
import sonmanobase.messaging as messaging

try:
    from son_mano_fpgalm import fpgalm_helpers as tools
except:
    import fpgalm_helpers as tools

try:
    from son_mano_fpgalm import fpgalm_topics as t
except:
    import fpgalm_topics as t

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:fpgalm")
LOG.setLevel(logging.INFO)


class FPGAServiceLifecycleManager(ManoBasePlugin):
    """
    This class implements the fpga service lifecycle manager.
    """

    def __init__(self,
                 auto_register=True,
                 wait_for_registration=True,
                 start_running=True):
        """
        Initialize class and son-mano-base.plugin.BasePlugin class.
        This will automatically connect to the broker, contact the
        plugin manager, and self-register this plugin to the plugin
        manager.

        After the connection and registration procedures are done, the
        'on_lifecycle_start' method is called.
        :return:
        """

        # Create the ledger that saves state
        self.fpga_services = {}
        self.fpgalm_ledger = {}
        self.thrd_pool = pool.ThreadPoolExecutor(max_workers=10)

        # call super class (will automatically connect to
        # broker and register the FLM to the plugin manger)
        ver = "0.1-dev"
        des = "This is the FPGA-LM plugin"

        super(self.__class__, self).__init__(version=ver,
                                             description=des,
                                             auto_register=auto_register,
                                             wait_for_registration=wait_for_registration,
                                             start_running=start_running)

    def __del__(self):
        """
        Destroy FPGALM instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics that CLM subscribes on.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        # The topic on which deploy requests are posted.
        self.manoconn.subscribe(self.fpga_service_instance_create, t.FPGA_DEPLOY)

    def on_lifecycle_start(self, ch, mthd, prop, msg):
        """
        This event is called when the plugin has successfully registered itself
        to the plugin manager and received its lifecycle.start event from the
        plugin manager. The plugin is expected to do its work after this event.

        :param ch: RabbitMQ channel
        :param method: RabbitMQ method
        :param properties: RabbitMQ properties
        :param message: RabbitMQ message content
        :return:
        """
        super(self.__class__, self).on_lifecycle_start(ch, mthd, prop, msg)
        LOG.info("FPGA-LM started and operational.")

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering FPGA-LM with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the FLM is registered to the plugin mananger
        """
        super(self.__class__, self).on_registration_ok()
        LOG.debug("Received registration ok event.")

##########################
# FGPALM Threading management
##########################

    def get_ledger(self, fpga_service_id):
        return self.fpga_services[fpga_service_id]

    def get_fpga_services(self):
        return self.fpga_services

    def set_fpga_services(self, fpga_service_dict):
        self.fpga_services = fpga_service_dict

        return

    def start_next_task(self, fpga_service_id):
        """
        This method makes sure that the next task in the schedule is started
        when a task is finished, or when the first task should begin.

        :param fpga_service_id: the inst uuid of the fpga service that is being handled.
        :param first: indicates whether this is the first task in a chain.
        """

        # If the kill field is active, the chain is killed
        if self.fpga_services[fpga_service_id]['kill_chain']:
            LOG.info("FPGA Service " + fpga_service_id + ": Killing running workflow")
            del self.fpga_services[fpga_service_id]
            return

        # Select the next task, only if task list is not empty
        if len(self.fpga_services[fpga_service_id]['schedule']) > 0:

            # share state with other FLMs
            next_task = getattr(self,
                                self.fpga_services[fpga_service_id]['schedule'].pop(0))

            # Push the next task to the threading pool
            task = self.thrd_pool.submit(next_task, fpga_service_id)

            # Log if a task fails
            if task.exception() is not None:
                print(task.result())

            # When the task is done, the next task should be started if no flag
            # is set to pause the chain.
            if self.fpga_services[fpga_service_id]['pause_chain']:
                self.fpga_services[fpga_service_id]['pause_chain'] = False
            else:
                self.start_next_task(fpga_service_id)

        else:
            del self.fpga_services[fpga_service_id]

####################
# CLM input - output
####################

    def fpgalm_error(self, fpga_service_id, error=None):
        """
        This method is used to report back errors to the SLM
        """
        if error is None:
            error = self.fpga_services[fpga_service_id]['error']
        LOG.info("FPGA Service " + fpga_service_id + ": error occured: " + error)
        LOG.info("FPGA Service " + fpga_service_id + ": informing FPGALM")

        message = {}
        message['status'] = "failed"
        message['error'] = error
        message['timestamp'] = time.time()

        corr_id = self.fpga_services[fpga_service_id]['orig_corr_id']
        topic = self.fpga_services[fpga_service_id]['topic']

        self.manoconn.notify(topic,
                             yaml.dump(message),
                             correlation_id=corr_id)

        # Kill the current workflow
        self.fpga_services[fpga_service_id]['kill_chain'] = True

    def fpga_service_instance_create(self, ch, method, properties, payload):
        """
        This fpga service handles a received message on the *.fpga_service.create
        topic.
        """

        # Don't trigger on self created messages
        if self.name == properties.app_id:
            return

        LOG.info("FPGA Service instance create request received.")
        message = yaml.load(payload)

        # Extract the correlation id
        corr_id = properties.correlation_id

        fpga_service_id = message['id']

        # Add the function to the ledger
        self.add_fpga_service_to_ledger(message, corr_id, fpga_service_id, t.FPGA_DEPLOY)

        # Schedule the tasks that the FLM should do for this request.
        add_schedule = []

        add_schedule.append("deploy_fpga_service")
        add_schedule.append("store_fpgar")
        add_schedule.append("inform_slm_on_deployment")

        self.fpga_services[fpga_service_id]['schedule'].extend(add_schedule)

        msg = ": New instantiation request received. Instantiation started."
        LOG.info("FPGA Service " + fpga_service_id + msg)
        # Start the chain of tasks
        self.start_next_task(fpga_service_id)

        return self.fpga_services[fpga_service_id]['schedule']

    def deploy_fpga_service(self, fpga_service_id):
        """
        This methods requests the deployment of a fpga service
        """

        fpga_service = self.fpga_services[fpga_service_id]

        outg_message = {}
        outg_message['fpgad'] = fpga_service['fpgad']
        outg_message['fpgad']['instance_uuid'] = fpga_service['id']
        outg_message['vim_uuid'] = fpga_service['vim_uuid']
        outg_message['service_instance_id'] = fpga_service['serv_id']

        payload = yaml.dump(outg_message)

        corr_id = str(uuid.uuid4())
        self.fpga_services[fpga_service_id]['act_corr_id'] = corr_id

        LOG.info("IA contacted for fpga service deployment.")
        LOG.debug("Payload of request: " + payload)
        # Contact the IA
        self.manoconn.call_async(self.ia_deploy_response,
                                 t.IA_DEPLOY,
                                 payload,
                                 correlation_id=corr_id)

        # Pause the chain of tasks to wait for response
        self.fpga_services[fpga_service_id]['pause_chain'] = True

    def ia_deploy_response(self, ch, method, prop, payload):
        """
        This method handles the response from the IA on the
        fpga service deploy request.
        """

        LOG.info("Response from IA on fpga service deploy call received.")
        LOG.debug("Payload of request: " + str(payload))

        inc_message = yaml.load(payload)

        fpga_service_id = tools.fpga_serviceid_from_corrid(self.fpga_services, prop.correlation_id)

        self.fpga_services[fpga_service_id]['status'] = inc_message['request_status']

        if inc_message['request_status'] == "COMPLETED":
            LOG.info("Cs deployed correctly")
            self.fpga_services[fpga_service_id]["ia_fpgar"] = inc_message["fpgar"]
            self.fpga_services[fpga_service_id]["error"] = None

        else:
            LOG.info("Deployment failed: " + inc_message["message"])
            self.fpga_services[fpga_service_id]["error"] = inc_message["message"]
            topic = self.fpga_services[fpga_service_id]['topic']
            self.fpgalm_error(fpga_service_id, topic)
            return

        self.start_next_task(fpga_service_id)

    def store_fpgar(self, fpga_service_id):
        """
        This method stores the fpgar in the repository
        """

        fpga_service = self.fpga_services[fpga_service_id]

        # Build the record
        fpgar = tools.build_fpgar(fpga_service['ia_fpgar'], fpga_service['fpgad'])
        self.fpga_services[fpga_service_id]['fpgar'] = fpgar
        LOG.info(yaml.dump(fpgar))

        # Store the record
        url = t.FPGAR_REPOSITORY_URL + 'fpga-instances'
        header = {'Content-Type': 'application/json'}
        fpgar_response = requests.post(url,
                                      data=json.dumps(fpgar),
                                      headers=header,
                                      timeout=1.0)
        LOG.info("Storing FPGAR on " + url)
        LOG.debug("FPGAR: " + str(fpgar))

        if fpgar_response.status_code == 200:
            LOG.info("FPGAR storage accepted.")
        # If storage fails, add error code and message to reply to gk
        else:
            error = {'http_code': fpgar_response.status_code,
                     'message': fpgar_response.json()}
            self.fpga_services[fpga_service_id]['error'] = error
            LOG.info('FPGAR to repo failed: ' + str(error))

        return

    def inform_slm_on_deployment(self, fpga_service_id):
        """
        In this method, the SLM is contacted to inform on the cs
        deployment.
        """
        LOG.info("Informing the SLM of the status of the fpga-service deployment")

        fpga_service = self.fpga_services[fpga_service_id]

        message = {}
        message["fpgar"] = fpga_service["fpgar"]
        message["status"] = fpga_service["status"]
        message["error"] = fpga_service["error"]

        corr_id = self.fpga_services[fpga_service_id]['orig_corr_id']
        self.manoconn.notify(t.FPGA_DEPLOY,
                             yaml.dump(message),
                             correlation_id=corr_id)


###########
# CLM tasks
###########

    def add_fpga_service_to_ledger(self, payload, corr_id, fpga_service_id, topic):
        """
        This method adds new fpga services with their specifics to the ledger,
        so other fpga services can use this information.

        :param payload: the payload of the received message
        :param corr_id: the correlation id of the received message
        :param fpga_service_id: the instance uuid of the fpga service defined by SLM.
        """

        # Add the fpga service to the ledger and add instance ids
        self.fpga_services[fpga_service_id] = {}
        self.fpga_services[fpga_service_id]['fpgad'] = payload['fpgad']
        self.fpga_services[fpga_service_id]['id'] = fpga_service_id

        # Add the topic of the call
        self.fpga_services[fpga_service_id]['topic'] = topic

        # Add to correlation id to the ledger
        self.fpga_services[fpga_service_id]['orig_corr_id'] = corr_id

        # Add payload to the ledger
        self.fpga_services[fpga_service_id]['payload'] = payload

        # Add the service uuid that this fpga service belongs to
        self.fpga_services[fpga_service_id]['serv_id'] = payload['serv_id']

        # Add the VIM uuid
        self.fpga_services[fpga_service_id]['vim_uuid'] = payload['vim_uuid']

        # Create the fpga service schedule
        self.fpga_services[fpga_service_id]['schedule'] = []

        # Create the chain pause and kill flag
        self.fpga_services[fpga_service_id]['pause_chain'] = False
        self.fpga_services[fpga_service_id]['kill_chain'] = False

        self.fpga_services[fpga_service_id]['act_corr_id'] = None
        self.fpga_services[fpga_service_id]['message'] = None

        # Add error field
        self.fpga_services[fpga_service_id]['error'] = None

        return fpga_service_id

    def recreate_ledger(self, payload, corr_id, fpga_server_id, topic):
        """
        This method adds already existing fpga services with their specifics
        back to the ledger, so other methods can use this information.

        :param payload: the payload of the received message
        :param corr_id: the correlation id of the received message
        :param fpga_server_id: the instance uuid of the fpga service defined by SLM.
        """

        # Add the fpga service to the ledger and add instance ids
        self.fpga_services[fpga_server_id] = {}

        fpgar = {}
        self.fpga_services[fpga_server_id]['fpgar'] = fpgar

        if 'fpgad' in payload.keys():
            fpgad = payload['fpgad']
        else:
            fpgad = {}
        self.fpga_services[fpga_server_id]['fpgad'] = fpgad

        self.fpga_services[fpga_server_id]['id'] = fpga_server_id

        # Add the topic of the call
        self.fpga_services[fpga_server_id]['topic'] = topic

        # Add to correlation id to the ledger
        self.fpga_services[fpga_server_id]['orig_corr_id'] = corr_id

        # Add payload to the ledger
        self.fpga_services[fpga_server_id]['payload'] = payload

        # Add the service uuid that this fpga service belongs to
        self.fpga_services[fpga_server_id]['serv_id'] = payload['serv_id']

        # Add the VIM uuid
        self.fpga_services[fpga_server_id]['vim_uuid'] = ''

        # Create the fpga service schedule
        self.fpga_services[fpga_server_id]['schedule'] = []

        # Create the chain pause and kill flag
        self.fpga_services[fpga_server_id]['pause_chain'] = False
        self.fpga_services[fpga_server_id]['kill_chain'] = False

        # Add error field
        self.fpga_services[fpga_server_id]['error'] = None

        return fpga_server_id


def main():
    """
    Entry point to start plugin.
    :return:
    """
    # reduce messaging log level to have a nicer output for this plugin
    logging.getLogger("son-mano-base:messaging").setLevel(logging.INFO)
    logging.getLogger("son-mano-base:plugin").setLevel(logging.INFO)
    # create our fpga service lifecycle manager
    fpgalm = FPGAServiceLifecycleManager()

if __name__ == '__main__':
    main()
