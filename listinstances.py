#!/usr/bin/env python
 
import oci
 
delegation_token = open('/etc/oci/delegation_token', 'r').read()
signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
  delegation_token=delegation_token
)

search_client = oci.resource_search.ResourceSearchClient({},signer=signer)
compute_client = oci.core.ComputeClient({},signer=signer)
network_client = oci.core.VirtualNetworkClient({},signer=signer)
identity_client = oci.identity.IdentityClient({},signer=signer)
 
try:
    resp = search_client.search_resources(
        oci.resource_search.models.StructuredSearchDetails(
            type="Structured",
            query="query instance resources where lifeCycleState != 'TERMINATED'"
        ), limit=1000
    )
except Exception as ex:
    print(ex)
lst = [
    'display_name',
    'private_ip',
    'public_ip',
    'lifecycle_state',
    'time_created',
    'compartment_name',
    'shape',
    'ocpus',
    'memory_in_gbs',
    'availability_domain',
    'fault_domain',
    'Subnet_Name',
    'Operating_system',
    'OS_Version'
]

resultString = ",".join([str(item) for item in lst if item])

print(resultString)

for instance in resp.data.items:
    resp = compute_client.list_vnic_attachments(
        compartment_id=instance.compartment_id,
        instance_id=instance.identifier
    )

    for vnic_attachment in resp.data:
        try:
            vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
            compute = compute_client.get_instance(instance_id=instance.identifier).data
            image_id = compute.image_id
            image_details = compute_client.get_image(image_id=image_id).data
            subnet_id = vnic.subnet_id
            subnet_details = network_client.get_subnet(subnet_id=subnet_id).data
            vcn_id = subnet_details.vcn_id

            compartment_details = identity_client.get_compartment(compartment_id=instance.compartment_id).data
            print(",".join([
                str(compute.display_name),
                str(vnic.private_ip),
                str(vnic.public_ip),
                str(compute.lifecycle_state),
                str(instance.time_created),
                str(compartment_details.name),
                str(compute.shape),
                str(compute.shape_config.ocpus),
                str(compute.shape_config.memory_in_gbs),
                str(compute.availability_domain),
                str(compute.fault_domain),
                str(subnet_details.display_name),
                str(image_details.operating_system),
                str(image_details.operating_system_version)
            ]))
        except Exception as ex1:
            print(ex1)
