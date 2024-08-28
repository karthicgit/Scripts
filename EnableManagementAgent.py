import oci


# To run in cloudshell
delegation_token = open('/etc/oci/delegation_token', 'r').read()
signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
   delegation_token=delegation_token
)

#list instances 
core_client = oci.core.ComputeClient(config={},signer=signer)

compartment_id = "<replace with compartment OCID>"


# list running instances in a compartment
list_instances_response = core_client.list_instances(
    compartment_id=compartment_id,
    lifecycle_state="RUNNING")
list_response = list_instances_response.data
for instance in list_response:
    get_image_response = core_client.get_image(image_id=instance.image_id)
    image_response = get_image_response.data
    if image_response.operating_system == "Oracle Linux":
        plugin_list = instance.agent_config.plugins_config
        for plugin in plugin_list:
            if plugin.name == "Management Agent" and plugin.desired_state == "DISABLED":
                plugin.desired_state = "ENABLED"
                print(f"Updating plugin for instance {instance.display_name}")
                update_instance_response = core_client.update_instance(
                    instance_id=instance.id,
                    update_instance_details=oci.core.models.UpdateInstanceDetails(
                        agent_config=oci.core.models.UpdateInstanceAgentConfigDetails(
                            is_monitoring_disabled=instance.agent_config.is_monitoring_disabled,
                            is_management_disabled=instance.agent_config.is_management_disabled,
                            are_all_plugins_disabled=instance.agent_config.are_all_plugins_disabled,
                            plugins_config=plugin_list)))
