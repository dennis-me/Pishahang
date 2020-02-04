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
import os
from datetime import datetime
from mongoengine import Document, connect, StringField, DictField, DateTimeField, BooleanField, ListField, signals, EmbeddedDocument, EmbeddedDocumentField

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("son-mano-pluginmanger:model")
LOG.setLevel(logging.INFO)



class AWSVIM(Document):
    vim_uuid = StringField(primary_key=True, required=True)
    access_key = StringField(required=True)
    secret_key = StringField(required=True)
    accountid = StringField(required=True)
    budgetname = StringField(required=True)

    def save(self, **kwargs):
        super().save(**kwargs)
        LOG.debug("Saved: %s" % self)


    def to_dict(self):
        """
        Convert to dict.
        (Yes, doing it manually isn't nice but its ok with a limited number of fields and gives us more control)
        :return:
        """
        res = dict()
        res["vim_uuid"] = self.vim_uuid
        res["access_key"] = self.access_key
        res["secret_key"] = self.secret_key
        res["accountid"] = self.accountid
        res["budgetname"] = self.budgetname
        return res

class AWSD(Document):
    """
    This model represents a plugin that is registered to the plugin manager.
    We use mongoengine as ORM to interact with MongoDB.
    """
    uuid = StringField(primary_key=True, required=True)
    name = StringField(required=True)
    descriptor_version = StringField(required=True)
    vendor = StringField(required=True)
    version = StringField(required=True)
    author = StringField()    
    licences = StringField()
    description = StringField()
    service_specific_managers = StringField()
    network_functions = StringField()
    cloud_services = StringField()
    fpga_services = StringField()
    connection_points = StringField()
    virtual_links = StringField()
    forwarding_graphs = StringField()
    lifecycle_events = StringField()
    vnf_dependency = StringField()
    services_dependency = StringField()
    monitoring_parameters = StringField()
    auto_scale_policy = StringField()

    


    def __repr__(self):
        return "AWSD(uuid=%r, name=%r, version=%r)" % (self.uuid, self.name, self.version)

    def __str__(self):
        return self.__repr__()

    def save(self, **kwargs):
        super().save(**kwargs)
        LOG.debug("Saved: %s" % self)

    def to_dict(self):
        """
        Convert to dict.
        (Yes, doing it manually isn't nice but its ok with a limited number of fields and gives us more control)
        :return:
        """
        res = dict()
        res["uuid"] = self.uuid
        res["name"] = self.name
        res["version"] = self.version
        res["vendor"] = self.vendor
        res["descriptor_version"] = self.descriptor_version
        res["author"] = self.author
        if self.description:
            res["description"] = self.description
        if self.licences:
            res["licences"] = self.licences
        if self.service_specific_managers:
            res["service_specific_managers"] = self.service_specific_managers
        if self.network_functions:
            res["network_functions"] = self.network_functions
        if self.cloud_services:
            res["cloud_services"] = self.cloud_services
        if self.fpga_services:
            res["fpga_services"] = self.fpga_services
        if self.connection_points:
            res["connection_points"] = self.connection_points
        if self.virtual_links:
            res["virtual_links"] = self.virtual_links
        if self.forwarding_graphs:
            res["forwarding_graphs"] = self.forwarding_graphs
        if self.lifecycle_events:
            res["lifecycle_events"] = self.lifecycle_events
        if self.vnf_dependency:
            res["vnf_dependency"] = self.vnf_dependency
        if self.services_dependency:
            res["services_dependency"] = self.services_dependency
        if self.monitoring_parameters:
            res["monitoring_parameters"] = self.monitoring_parameters
        if self.auto_scale_policy:
            res["auto_scale_policy"] = self.auto_scale_policy


        return res


class AWSR(Document):
    """
    This model represents a plugin that is registered to the plugin manager.
    We use mongoengine as ORM to interact with MongoDB.
    """
    uuid = StringField(primary_key=True, required=True)
    myid = StringField(required=True)
    status = StringField(required=True)
    descriptor_version = StringField(required=True)
    version = StringField()
    descriptor_reference = StringField()
    network_functions = ListField()
    cloud_services = ListField()
    fpga_services = ListField()
    connection_points = ListField()
    virtual_links = ListField()
    forwarding_graphs = ListField()
    lifecycle_events = ListField()
    vnf_dependency = ListField()
    services_dependency = ListField()
    monitoring_parameters = ListField()
    auto_scale_policy = ListField()





    def __repr__(self):
        return "AWSR(uuid=%r, version=%r)" % (self.uuid, self.version)

    def __str__(self):
        return self.__repr__()

    def save(self, **kwargs):
        super().save(**kwargs)
        LOG.debug("Saved: %s" % self)

    def to_dict(self):
        """
        Convert to dict.
        (Yes, doing it manually isn't nice but its ok with a limited number of fields and gives us more control)
        :return:
        """
        res = dict()
        res["uuid"] = self.uuid
        res["id"] = self.myid
        res["descriptor_version"] = self.descriptor_version
        res["status"] = self.status
        if self.version:
            res["version"] = self.version
        if self.descriptor_reference:
            res["descriptor_reference"] = self.descriptor_reference
        if self.network_functions:
            res["network_functions"] = self.network_functions
        if self.cloud_services:
            res["cloud_services"] = self.cloud_services
        if self.fpga_services:
            res["fpga_services"] = self.fpga_services
        if self.connection_points:
            res["connection_points"] = self.connection_points
        if self.virtual_links:
            res["virtual_links"] = self.virtual_links
        if self.forwarding_graphs:
            res["forwarding_graphs"] = self.forwarding_graphs
        if self.lifecycle_events:
            res["lifecycle_events"] = self.lifecycle_events
        if self.vnf_dependency:
            res["vnf_dependency"] = self.vnf_dependency
        if self.services_dependency:
            res["services_dependency"] = self.services_dependency
        if self.monitoring_parameters:
            res["monitoring_parameters"] = self.monitoring_parameters
        if self.auto_scale_policy:
            res["auto_scale_policy"] = self.auto_scale_policy

        return res


class FPGAD(Document):
    """
    This model represents a plugin that is registered to the plugin manager.
    We use mongoengine as ORM to interact with MongoDB.
    """
    uuid = StringField(primary_key=True, required=True)
    name = StringField(required=True)
    descriptor_version = StringField(required=True)
    vendor = StringField(required=True)
    version = StringField(required=True)
    virtual_deployment_units = StringField(required=True)
    author = StringField()
    description = StringField()
    licences = StringField()
    monitoring_rules = StringField()



    def __repr__(self):
        return "FPGAD(uuid=%r, name=%r, version=%r)" % (self.uuid, self.name, self.version)

    def __str__(self):
        return self.__repr__()

    def save(self, **kwargs):
        super().save(**kwargs)
        LOG.debug("Saved: %s" % self)

    def to_dict(self):
        """
        Convert to dict.
        (Yes, doing it manually isn't nice but its ok with a limited number of fields and gives us more control)
        :return:
        """
        res = dict()

        res["uuid"] = self.uuid
        res["name"] = self.name
        res["version"] = self.version
        res["vendor"] = self.vendor
        res["descriptor_version"] = self.descriptor_version
        res["virtual_deployment_units"] = self.virtual_deployment_units

        if self.description:
            res["description"] = self.description
        if self.licences:
            res["licences"] = self.licences
        if self.author:
            res["author"] = self.author
        if self.monitoring_rules:
            res["monitoring_rules"] = self.monitoring_rules


        return res


class FPGAR(Document):
    """
    This model represents a plugin that is registered to the plugin manager.
    We use mongoengine as ORM to interact with MongoDB.
    """
    uuid = StringField(primary_key=True, required=True)
    myid = StringField(required=True)
    descriptor_version = StringField(required=True)
    status = StringField(required=True)
    virtual_deployment_units = StringField(required=True)
    version = StringField()    
    parent_ns = ListField(StringField())
    descriptor_reference = StringField()




    def __repr__(self):
        return "FPGAR(uuid=%r, version=%r)" % (self.uuid, self.version)

    def __str__(self):
        return self.__repr__()

    def save(self, **kwargs):
        super().save(**kwargs)
        LOG.debug("Saved: %s" % self)

    def to_dict(self):
        """
        Convert to dict.
        (Yes, doing it manually isn't nice but its ok with a limited number of fields and gives us more control)
        :return:
        """
        res = dict()
        res["uuid"] = self.uuid
        res["id"] = self.myid
        res["status"] = self.status
        res["descriptor_version"] = self.descriptor_version
        res["virtual_deployment_units"] = self.virtual_deployment_units
        if self.version:
            res["version"] = self.version
        if self.parent_ns:
            res["parent_ns"] = self.parent_ns
        if self.descriptor_reference:
            res["descriptor_reference"] = self.descriptor_reference

        return res




def initialize(db="sonata-plugin-manager",
               host=os.environ.get("mongo_host", "127.0.0.1"),
               port=int(os.environ.get("mongo_port", 27017)),
               clear_db=True):
    db_conn = connect(db, host=host, port=port)
    LOG.info("Connected to MongoDB %r@%s:%d" % (db, host, port))
    if clear_db:
        # remove all old data from DB
        db_conn.drop_database(db)
        LOG.info("Cleared DB %r" % db)
