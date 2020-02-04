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

"""
Adds a REST interface to the plugin manager to control plugins registered to the platfoem.
"""
import logging
import threading
import yaml
import uuid as uid
import time
import json
from flask import Flask, request
import flask_restful as fr
from mongoengine import DoesNotExist
import model
import messaging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("son-mano-pluginmanger:interface")
LOG.setLevel(logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)




class AWSDEndpoint(fr.Resource):

    def get(self):
        LOG.debug("GET awsd list")
        return [p.uuid for p in model.AWSD.objects], 200

    def post(self):
        LOG.debug("Post request for AWSD")
        try:
            # get target state from request body
            req = request.json
            args = {}
            if "description" in req:
                args["description"] = req["description"]
            if "licences" in req:
                args["licences"] = json.dumps(req["licences"])
            if "service_specific_managers" in req:
                args["service_specific_managers"] = json.dumps(req["service_specific_managers"])
            if "network_functions" in req:
                args["network_functions"] = json.dumps(req["network_functions"])
            if "cloud_services" in req:
                args["cloud_services"] = json.dumps(req["cloud_services"])
            if "fpga_services" in req:
                args["fpga_services"] = json.dumps(req["fpga_services"])
            if "connection_points" in req:
                args["connection_points"] = json.dumps(req["connection_points"])
            if "virtual_links" in req:
                args["virtual_links"] = json.dumps(req["virtual_links"])
            if "forwarding_graphs" in req:
                args["forwarding_graphs"] = json.dumps(req["forwarding_graphs"])
            if "lifecycle_events" in req:
                args["lifecycle_events"] = json.dumps(req["lifecycle_events"])
            if "vnf_dependency" in req:
                args["vnf_dependency"] = json.dumps(req["vnf_dependency"])
            if "services_dependency" in req:
                args["services_dependency"] = json.dumps(req["services_dependency"])
            if "monitoring_parameters" in req:
                args["monitoring_parameters"] = json.dumps(req["monitoring_parameters"])
            if "auto_scale_policy" in req:
                args["auto_scale_policy"] = json.dumps(req["auto_scale_policy"])
                
            myuuid = str(uid.uuid4())


            p = model.AWSD(
                uuid = myuuid,
                name = req["name"],
                descriptor_version =req["descriptor_version"],
                vendor = req["vendor"],
                version = req["version"],
                author = req["author"],
                **args
                )     
            p.save()
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            return str(p.to_dict())+"Timestamp: "+ str(current_time), 200
        except DoesNotExist as e:
            LOG.error("Lookup error")
            return {}, 404




class AWSDEndpoints(fr.Resource):


    def delete(self, uuid=None):
        LOG.debug("DELETE AWSD: %r" % uuid)
        try:
            p = model.AWSD.objects.get(uuid=uuid)
            p.delete()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404
    
    def get(self, uuid=None):
        LOG.debug("GET plugin info for: %r" % uuid)
        try:
            p = model.AWSD.objects.get(uuid=uuid)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404

class AWSREndpoint(fr.Resource):

    def get(self):
        LOG.debug("GET awsr list")
        return [p.uuid for p in model.AWSR.objects], 200

    def post(self):
        LOG.debug("Post request for AWSR")
        try:
            # get target state from request body
            req = request.json
            args = {}
            if "version" in req:
                args["version"] = req["version"]
            if "descriptor_reference" in req:
                args["descriptor_reference"] = req["descriptor_reference"]
            if "network_functions" in req:
                args["network_functions"] = req["network_functions"]
            if "cloud_services" in req:
                args["cloud_services"] = req["cloud_services"]
            if "fpga_services" in req:
                args["fpga_services"] = req["fpga_services"]
            if "connection_points" in req:
                args["connection_points"] = req["connection_points"]
            if "virtual_links" in req:
                args["virtual_links"] = req["virtual_links"]
            if "forwarding_graphs" in req:
                args["forwarding_graphs"] = req["forwarding_graphs"]
            if "lifecycle_events" in req:
                args["lifecycle_events"] = req["lifecycle_events"]
            if "vnf_dependency" in req:
                args["vnf_dependency"] = req["vnf_dependency"]
            if "services_dependency" in req:
                args["services_dependency"] = req["services_dependency"]
            if "monitoring_parameters" in req:
                args["monitoring_parameters"] = req["monitoring_parameters"]
            if "auto_scale_policy" in req:
                args["auto_scale_policy"] = req["auto_scale_policy"]


            p = model.AWSR(
                uuid = str(uid.uuid4()),
                myid = req["id"],
                descriptor_version =req["descriptor_version"],
                status = req["status"],
                **args
                )   
            p.save()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error")
            return {}, 404



class AWSREndpoints(fr.Resource):


    def delete(self, uuid=None):
        LOG.debug("DELETE AWSR: %r" % uuid)
        try:
            p = model.AWSR.objects.get(uuid=uuid)
            p.delete()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404
    
    def get(self, uuid=None):
        LOG.debug("GET plugin info for: %r" % uuid)
        try:
            p = model.AWSR.objects.get(uuid=uuid)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404


class FPGADEndpoint(fr.Resource):

    def get(self):
        LOG.debug("GET fpgad list")
        return [p.uuid for p in model.FPGAD.objects], 200


    def post(self):
        LOG.debug("Post request for FPGAD")
        try:
            # get target state from request body
            req = request.json
            args = {}
            if "author" in req:
                args["author"] = req["author"]
            if "description" in req:
                args["description"] = req["description"]
            if "licences" in req:
                args["licences"] = json.dumps(req["licences"])
            if "monitoring_rules" in req:
                args["monitoring_rules"] = json.dumps(req["monitoring_rules"])

            uuid = str(uid.uuid4())
            p = model.FPGAD(
                uuid = uuid,
                name = req["name"],
                descriptor_version =req["descriptor_version"],
                vendor = req["vendor"],
                version = req["version"],
                virtual_deployment_units = json.dumps(req["virtual_deployment_units"]),
                **args
                )   
            p.save()
            return uuid, 200
        except DoesNotExist as e:
            LOG.error("Lookup error")
            return {}, 404




class FPGADEndpoints(fr.Resource):

    def delete(self, uuid=None):
        LOG.debug("DELETE FPGAD: %r" % uuid)
        try:
            p = model.FPGAD.objects.get(uuid=uuid)
            p.delete()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404
    
    def get(self, uuid=None):
        LOG.debug("GET plugin info for: %r" % uuid)
        try:
            p = model.FPGAD.objects.get(uuid=uuid)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404


class FPGAREndpoint(fr.Resource):

    def get(self):
        LOG.debug("GET fpgar list")
        return [p.uuid for p in model.FPGAR.objects], 200

    def post(self):
        LOG.debug("Post request for FPGAR")
        try:
            # get target state from request body
            req = request.json
            print(req)
            args = {}
            if "version" in req:
                args["version"] = req["version"]
            if "parent_ns" in req:
                args["parent_ns"] = req["parent_ns"]
            if "descriptor_reference" in req:
                args["descriptor_reference"] = req["descriptor_reference"]

            p = model.FPGAR(
                uuid = str(uid.uuid4()),
                descriptor_version =req["descriptor_version"],
                myid = req["id"],
                status = req["status"],
                virtual_deployment_units = json.dumps(req["virtual_deployment_units"]),
                **args
                )   
            p.save()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error")
            return {}, 404



class FPGAREndpoints(fr.Resource):


    def put(self, uuid=None):
        LOG.debug("PUT : %r" % uuid)
        try:
            p = model.FPGAR.objects.get(myid=uuid)
            # get target state from request body
            req = request.json
            print(req)
            print(p)
            if req is None:
                LOG.error("Malformed request: %r" % request.json)
                return {"message": "malformed request"}, 500
            else:
                return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404


    def delete(self, uuid=None):
        LOG.debug("DELETE FPGAR: %r" % uuid)
        try:
            p = model.FPGAR.objects.get(uuid=uuid)
            p.delete()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404
    
    def get(self, uuid=None):
        LOG.debug("GET plugin info for: %r" % uuid)
        try:
            p = model.FPGAR.objects.get(uuid=uuid)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % uuid)
            return {}, 404


class RequestEndpoint(fr.Resource):

    # all list objects need to be stored as string, because list objects in mongoengine add unwanted metadata 
    def deserializeFpgadLists(self, fpgad):
        fpgad["virtual_deployment_units"] = json.loads(fpgad["virtual_deployment_units"])
        if "licences" in fpgad:
            fpgad["licences"] = json.loads(fpgad["licences"])
        if "monitoring_rules" in fpgad:
            fpgad["monitoring_rules"] = json.loads(fpgad["monitoring_rules"])
        return fpgad

    def deserializeAwsLists(self, awsd):
        if "fpga_services" in awsd:
            awsd['fpga_services'] = json.loads(awsd['fpga_services'])
        if "cloud_services" in awsd:
            awsd["cloud_services"] = json.loads(awsd["cloud_services"])
        if "network_functions" in awsd:
            awsd["network_functions"] = json.loads(awsd["network_functions"])
        if "service_specific_managers" in awsd:
            awsd["service_specific_managers"] = json.loads(awsd["service_specific_managers"])
        if "licences" in awsd:
            awsd["licences"] = json.loads(awsd["licences"])
        if "connection_points" in awsd:
            awsd["connection_points"] = json.loads(awsd["connection_points"])
        if "virtual_links" in awsd:
            awsd["virtual_links"] = json.loads(awsd["virtual_links"])                                        
        if "forwarding_graphs" in awsd:
            awsd["forwarding_graphs"] = json.loads(awsd["forwarding_graphs"])
        if "lifecycle_events" in awsd:
            awsd["lifecycle_events"] = json.loads(awsd["lifecycle_events"])
        if "vnf_dependency" in awsd:
            awsd["vnf_dependency"] = json.loads(awsd["vnf_dependency"])
        if "services_dependency" in awsd:
            awsd["services_dependency"] = json.loads(awsd["services_dependency"])
        if "monitoring_parameters" in awsd:
            awsd["monitoring_parameters"] = json.loads(awsd["monitoring_parameters"])                                        
        if "auto_scale_policy" in awsd:
            awsd["auto_scale_policy"] = json.loads(awsd["auto_scale_policy"])
                        
        return awsd

    def deleteRecords(self, serv_id):
        # delete aws records
        try:
            p = model.AWSR.objects.get(descriptor_reference=serv_id)
            p.delete()
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % serv_id)
            return {}, 404
        # delete fpga records related to the aws service
        try:
            for fpgar in model.FPGAR.objects:
                fpgar["virtual_deployment_units"] = json.loads(fpgar["virtual_deployment_units"])
                if fpgar["descriptor_reference"] == serv_id:
                    vim_uuid = fpgar["virtual_deployment_units"][0]["vim_id"]
                    fpgar.delete()
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % serv_id)
            return {}, 404
        return vim_uuid

    def on_publish_response(self, ch, method, props, response):
        response = yaml.load(str(response))
        if type(response) == dict:
            try:
                print(response)
            except BaseException as error:
                print(error)
    def on_terminate_response(self, ch, method, props, response):
        response = yaml.load(str(response))
        if type(response) == dict:
            try:
                print(response)
            except BaseException as error:
                print(error)

    def post(self):
        LOG.debug("MAKE an instance request")
        req = request.json

        manoconn = messaging.ManoBrokerRequestResponseConnection("request.instance")

        # check if instantiation or termination
        if "request_type" not in req:
            # get descriptors with uuid
            try:
                awsd = model.AWSD.objects.get(uuid=req["service_uuid"])
            except DoesNotExist as e:
                LOG.error("Lookup error: %r" % req["service_uuid"])
                return {}, 404

            aws_descriptor = self.deserializeAwsLists(awsd.to_dict())
            service_name = aws_descriptor["name"]
            
            fpga_descriptors = {}
            i = 0

            # iterate through all fpgads and find all service related fpgads
            try:
                for fpgad in model.FPGAD.objects:
                    if fpgad.name == service_name:
                        descriptor = self.deserializeFpgadLists(fpgad.to_dict())
                        descriptor["uuid"] = req["service_uuid"]
                        fpga_descriptors["FPGAD"+ str(i)] = descriptor
                        i += 1
            except DoesNotExist as e:
                LOG.error("Lookup error: %r" % service_name)
                return {}, 404

            LOG.info("Sending instantiate request")

            message = {'AWSD': aws_descriptor, 'uuid': req["service_uuid"], "user_data" : "", **fpga_descriptors}
            manoconn.call_async(self.on_publish_response,
                                     'service.instances.create',
                                     yaml.dump(message))
        else:
            vim_uuid = self.deleteRecords(req['service_instance_uuid'])
            message = {"instance_id": req["service_instance_uuid"], "vim_uuid":vim_uuid}
            manoconn.call_async(self.on_terminate_response,
                                     'infrastructure.service.fpga.terminate',
                                     yaml.dump(message))




class VIMEndpoint(fr.Resource):

    def get(self):
        LOG.debug("GET vim list")
        return [p.vim_uuid for p in model.AWSVIM.objects], 200

    def post(self):
        LOG.debug("Post request for vims")
        try:
            # get target state from request body
            req = request.json
                
            p = model.AWSVIM(
                vim_uuid = str(uid.uuid4()),
                access_key = req["access_key"],
                secret_key =req["secret_key"],
                accountid = req["accountid"],
                budgetname = req["budgetname"],
                )     
            p.save()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error")
            return {}, 404



class VIMEndpoints(fr.Resource):


    def get(self, vim_uuid=None):
        LOG.debug("GET vim info for: %r" % vim_uuid)
        try:
            p = model.AWSVIM.objects.get(vim_uuid=vim_uuid)
            return p.to_dict(), 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % vim_uuid)
            return {}, 404

    def delete(self, vim_uuid=None):
        LOG.debug("DELETE VIM: %r" % vim_uuid)
        try:
            p = model.AWSVIM.objects.get(vim_uuid=vim_uuid)
            p.delete()
            return {}, 200
        except DoesNotExist as e:
            LOG.error("Lookup error: %r" % vim_uuid)
            return {}, 404
    

PM = None
# setup Flask
app = Flask(__name__)
api = fr.Api(app)
# register endpoints
api.add_resource(AWSDEndpoint, "/awsds")
api.add_resource(AWSDEndpoints, "/awsds/<string:uuid>")
api.add_resource(AWSREndpoint, "/awsrs")
api.add_resource(AWSREndpoints, "/awsrs/<string:uuid>")
api.add_resource(FPGADEndpoint, "/fpgads")
api.add_resource(FPGADEndpoints, "/fpgads/<string:uuid>")
api.add_resource(FPGAREndpoint, "/fpgars")
api.add_resource(FPGAREndpoints, "/fpgars/<string:uuid>")
api.add_resource(RequestEndpoint, "/requests")
api.add_resource(VIMEndpoint, "/vim")
api.add_resource(VIMEndpoints, "/vim/<string:vim_uuid>")



def _start_flask(host, port):
    # start the Flask server (not the best performance but ok for our use case)
    app.run(host=host,
            port=port,
            debug=True,
            use_reloader=False  # this is needed to run Flask in a non-main thread
            )


def start(pm, host="0.0.0.0", port=8008):
    global PM
    PM = pm
    thread = threading.Thread(target=_start_flask, args=(host, port))
    thread.daemon = True
    thread.start()
    LOG.info("Started management REST interface @ http://%s:%d" % (host, port))
model.initialize()
start(PM)
while True:
    time.sleep(5)