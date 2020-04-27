try:
    from fpga_wrapper import fpga_helper as helper
except:
    import fpga_helper as helper

try:
    from fpga_wrapper import fpga_messaging as messaging
except:
    import fpga_messaging as messaging
    
import logging
import time
import yaml
import uuid
import boto3
import requests
import json



logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:fpga_wrapper")
LOG.setLevel(logging.INFO)



class FPGAServiceWrapper(object):
    def __init__(self):
        self.name = "%s.%s" % ('fpga-wrapper', self.__class__.__name__)
        LOG.info("Connecting to the message broker." )
        #init connection to broker
        while True:
            try:
                self.manoconn = messaging.ManoBrokerRequestResponseConnection(self.name)
                break
            except:
                time.sleep(5)
        LOG.info("Connected successfully to the message broker." )
        self.service = {}
        self.declare_subscriptions()
        self.run()


    def run(self):
        while True:
            time.sleep(1)

    def on_plugin_status_update(self, ch, method, properties, message):
        """
        To be overwritten by subclass.
        Called when a plugin list status update
        is received from the plugin manager.
        """
        LOG.debug("Received plugin status update %r." % str(message))

    def declare_subscriptions(self):
        #declaring all subscriptions to the message broker

        self.manoconn.register_async_endpoint(self.deploy_fpga,'infrastructure.fpga_service.deploy')
        self.manoconn.register_async_endpoint(self.returnTopology,'infrastructure.service.aws.topology')
        self.manoconn.register_async_endpoint(self.terminate_fpga,'infrastructure.service.fpga.terminate')



    def deploy_fpga(self,ch, method, properties, payload):
        #deploy fpga and respond accordingly
        LOG.info("FPGA Service instance create request received.")
        message = yaml.load(payload)

        #get information from the fpgad
        fpga_service_id = message['fpgad']['instance_uuid']
        serv_id = message['fpgad']['uuid']
        if serv_id in self.service:
            self.service[serv_id].append(fpga_service_id)
        else:
            self.service[serv_id] = [fpga_service_id]
        #start instantiation

        #get access/secret key
        vim_uuid = message['vim_uuid']
        url = helper.VIM_URL
        response = requests.get(url + "/"+ vim_uuid, timeout=1.0)
        
        dict_response = json.loads(response.text)
        access_key = dict_response['access_key']
        secret_key = dict_response['secret_key']
        tf_output = helper.startFPGAservice(helper.createTerraformDirectory(fpga_service_id), message,access_key,secret_key,fpga_service_id)
        if 'request status' not in message:
            if tf_output:
                message['fpgar'] = helper.createFPGAR(tf_output, message)
                message['request_status'] = "COMPLETED"
            else:
                LOG.info("Instance could not be deployed.")
                message['request_status'] = "FAILED"
                message['message'] = "Terraform could not instantiate instance"
            payload = yaml.dump(message)
            LOG.info("FPGALM has been contacted")
            return payload


    def returnTopology(self,ch, method, properties, payload):
        #connect to aws
        client = boto3.client('budgets')
        
        # get available vims

        url = helper.VIM_URL
        response = requests.get(url, timeout=1.0)
        vim_list = json.loads(response.text)


        message = []
        for vims in vim_list:
            response = requests.get(url + "/" + vims, timeout=1.0)
            dict = json.loads(response.text)
            

            client = boto3.client(
            'budgets',
            aws_access_key_id=dict["access_key"],
            aws_secret_access_key=dict["secret_key"]
            )

            #request monthly budget
            response = client.describe_budget(
            AccountId=dict["accountid"],
            BudgetName=dict["budgetname"]
            )
        #calculate rest amount
            budget_left = float(response['Budget']['BudgetLimit']['Amount'])-float(response['Budget']['CalculatedSpend']['ActualSpend']['Amount'])
            # one instance type will cost at ~2$
            message.append({'vim_type' : 'AWS','fpgas_left': int(budget_left/2),'vim_uuid': dict["vim_uuid"]})

        LOG.info("Topology request received.")
        return yaml.dump(message)

    def terminate_fpga(self,ch, method, properties, payload):

        LOG.info("FPGA Service instance terminate request received.")
        message = yaml.load(payload)
        serv_id = message['instance_id']
        vim_uuid = message['vim_uuid']
        url = helper.VIM_URL
        response = requests.get(url + "/"+ vim_uuid, timeout=1.0)
        
        dict_response = json.loads(response.text)
        access_key = dict_response['access_key']
        secret_key = dict_response['secret_key']
        if serv_id in self.service:
            #iterate through all fpgas related to the service and terminate all
            for fpga_service_id in self.service[serv_id]:
                helper.terminateFPGAservice(helper.createTerraformDirectory(fpga_service_id), secret_key, access_key)
            message['request_status'] = "COMPLETED"
        else:
            message['message'] = "Instance UUID does not exist."
        return yaml.dump(message)


def main():
    FPGAServiceWrapper()

if __name__ == '__main__':
    main()
