import os
import shutil
import python_terraform
import pathlib

VIM_URL = "http://0.0.0.0:8008/vim"

def createTerraformDirectory(inputpath):
    path = returnDirectory()
    newpath = path + '/' + inputpath
    try:
        os.mkdir(newpath)
    except OSError:
        print ('Terraform directory already exists at ' + newpath)
    else:
        print ('Terraform directory instantiated ' + newpath)

    shutil.copy(path + '/TerraformTemplate/main.tf', newpath)
    shutil.copy(path + '/TerraformTemplate/var.tf', newpath)
    shutil.copy(path + '/TerraformTemplate/instance.tf', newpath)
    return newpath

def returnDirectory():
    return str(pathlib.Path(__file__).parent.absolute())

def removeDirectory(path):
    shutil.rmtree(path)

def startFPGAservice(working_directory, message, access_key, secret_key, service_name):
    ami = message['fpgad']['virtual_deployment_units'][0]['ami']
    region = message['fpgad']['virtual_deployment_units'][0]['region']
    instance_type = message['fpgad']['virtual_deployment_units'][0]['instance_type']
    
    tf = python_terraform.Terraform(working_dir=working_directory)
    tf.init()
    tf.apply('-auto-approve', var={'ami_instance_id': ami, 'access_key_var': access_key, 'secret_key_var': secret_key,
                                   'instance_name': service_name, 'instance_type': instance_type, 'region': region})
    return tf.output()

def terminateFPGAservice(working_directory, secret_key, access_key):
    tf = python_terraform.Terraform(working_dir=working_directory)
    tf.destroy('-auto-approve', var={'secret_key_var': secret_key, 'access_key_var': access_key})
    removeDirectory(working_directory)
    
def createFPGAR(tf_output, message):



    fpgar = {}
    # fpgad base fields
    fpgar['descriptor_version'] = "0.1"
    fpgar['id'] = message['fpgad']['instance_uuid']
    # Building the fpgar makes it the first version of this fpgar.
    fpgar['status'] = "normal operation"
    if 'uuid' in message['fpgad']:
        fpgar['descriptor_reference'] = message['fpgad']['uuid']

    # virtual_deployment_units
    
    fpgar['virtual_deployment_units'] = []
    fpgar['virtual_deployment_units'] = ['vdu']
    fpgar['virtual_deployment_units'][0] = {}
    fpgar['virtual_deployment_units'][0]['vdu_reference'] = message['fpgad']['virtual_deployment_units'][0]['id']
    fpgar['virtual_deployment_units'][0]['id'] = message['fpgad']['virtual_deployment_units'][0]['name']
    fpgar['virtual_deployment_units'][0]['vim_id'] = message['vim_uuid']
    fpgar['virtual_deployment_units'][0]['ami'] = message['fpgad']['virtual_deployment_units'][0]['ami']
    fpgar['virtual_deployment_units'][0]['arn'] = tf_output['arn']['value'][0]
    fpgar['virtual_deployment_units'][0]['availability_zone'] = tf_output['availability_zone']['value'][0]
    fpgar['virtual_deployment_units'][0]['credit_specification'] = tf_output['credit_specification']['value'][0]
    fpgar['virtual_deployment_units'][0]['ebs_block_device_volume_ids'] = tf_output['ebs_block_device_volume_ids']['value'][0]
    fpgar['virtual_deployment_units'][0]['ids'] = tf_output['ids']['value'][0]
    fpgar['virtual_deployment_units'][0]['instance_state'] = tf_output['instance_state']['value'][0]
    fpgar['virtual_deployment_units'][0]['ipv6_addresses'] = tf_output['ipv6_addresses']['value'][0]
    fpgar['virtual_deployment_units'][0]['key_name'] = tf_output['key_name']['value'][0]
    fpgar['virtual_deployment_units'][0]['password_data'] = tf_output['password_data']['value'][0]
    fpgar['virtual_deployment_units'][0]['placement_group'] = tf_output['placement_group']['value'][0]
    fpgar['virtual_deployment_units'][0]['primary_network_interface_id'] = tf_output['primary_network_interface_id']['value'][0]
    fpgar['virtual_deployment_units'][0]['private_ip'] = tf_output['private_ip']['value'][0]
    fpgar['virtual_deployment_units'][0]['public_ip'] = tf_output['public_ip']['value'][0]
    fpgar['virtual_deployment_units'][0]['root_block_device_volume_ids'] = tf_output['root_block_device_volume_ids']['value'][0]
    fpgar['virtual_deployment_units'][0]['security_groups'] = tf_output['security_groups']['value'][0]
    fpgar['virtual_deployment_units'][0]['subnet_id'] = tf_output['subnet_id']['value'][0]
    fpgar['virtual_deployment_units'][0]['volume_tags'] = tf_output['volume_tags']['value'][0]
    fpgar['virtual_deployment_units'][0]['vpc_security_group_ids'] = tf_output['vpc_security_group_ids']['value'][0]

    return fpgar
