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
 
resp = search_client.search_resources(
  oci.resource_search.models.StructuredSearchDetails(
  type="Structured",
  query="query instance resources"
  )
)

 
for instance in resp.data.items:
  resp = compute_client.list_vnic_attachments(
  compartment_id=instance.compartment_id,
  instance_id=instance.identifier
  )
 
  for vnic_attachment in resp.data:
    vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
    compute = compute_client.get_instance(instance_id=instance.identifier).data
    compartment_details = identity_client.get_compartment(compartment_id=instance.compartment_id).data
    print(",".join([
    compute.display_name,
    vnic.private_ip,
    str(vnic.public_ip),
    compute.lifecycle_state,
    str(instance.time_created),
    compartment_details.name,
    compute.shape,
    str(compute.shape_config.ocpus),
    str(compute.shape_config.memory_in_gbs),
    compute.availability_domain,
    compute.fault_domain
    ]))