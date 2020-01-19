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
This contains helper functions for `clm.py`.
"""

import requests
import uuid
import yaml

def fpga_serviceid_from_corrid(ledger, corr_id):
    """
    This method returns the fpga service uuid based on a correlation id.
    It is used for responses from different modules that use the
    correlation id as reference instead of the fpga service id.

    :param serv_dict: The ledger of functions
    :param corr_id: The correlation id
    """

    for fpga_service_id in ledger.keys():
        if isinstance(ledger[fpga_service_id]['act_corr_id'], list):
            if str(corr_id) in ledger[fpga_service_id]['act_corr_id']:
                break
        else:
            if ledger[fpga_service_id]['act_corr_id'] == str(corr_id):
                break

    return fpga_service_id

def build_fpgar(ia_fpgar, fpgad):
    """
    This method builds the FPGARs. FPGARs are built from the stripped FPGARs
    returned by the Infrastructure Adaptor (IA), combining it with the
    provided FPGAD.
    """

    fpgar = {}
    # fpgad base fields
    fpgar['descriptor_version'] = ia_fpgar['descriptor_version']
    fpgar['id'] = ia_fpgar['id']
    # Building the fpgar makes it the first version of this fpgar.
    fpgar['version'] = '1'
    fpgar['status'] = ia_fpgar['status']
    fpgar['descriptor_reference'] = ia_fpgar['descriptor_reference']
    # virtual_deployment_units
    fpgar['virtual_deployment_units'] = []
    for ia_vdu in ia_fpgar['virtual_deployment_units']:
        fpgad_vdu = get_fpgad_vdu_by_reference(fpgad, ia_vdu['vdu_reference'])

        vdu = {}
        vdu['id'] = ia_vdu['id']
        vdu['vim_id'] = ia_vdu['vim_id']
        if 'resource_requirements' in fpgad_vdu:
            vdu['resource_requirements'] = fpgad_vdu['resource_requirements']

        vdu['service_image'] = fpgad_vdu['service_image']
        vdu['service_type'] = fpgad_vdu['service_type']

        if 'service_name' in fpgad_vdu:
            vdu['service_name'] = fpgad_vdu['service_name']

        if 'environment' in fpgad_vdu:
            vdu['environment'] = fpgad_vdu['environment']

        # vdu optional info
        if 'vdu_reference' in ia_vdu:
            vdu['vdu_reference'] = ia_vdu['vdu_reference']
        if 'number_of_instances' in ia_vdu:
            vdu['number_of_instances'] = ia_vdu['number_of_instances']

        if fpgad_vdu is not None and 'monitoring_parameters' in fpgad_vdu:
            vdu['monitoring_parameters'] = fpgad_vdu['monitoring_parameters']

        fpgar['virtual_deployment_units'].append(vdu)

    return fpgar

def get_fpgad_vdu_by_reference(fpgad, vdu_reference):
    if 'virtual_deployment_units' in fpgad:
        for fpgad_vdu in fpgad['virtual_deployment_units']:
            if fpgad_vdu['id'] in vdu_reference:
                return fpgad_vdu
    return None