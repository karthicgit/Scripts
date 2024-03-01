#!/bin/bash
compartment_id=<placeholder for comaprtment OCID>
for nsg_id in $(oci network nsg list -c $compartment_id | jq -r '.data[].id')
do
    for vnic_id in $(oci network nsg vnics list --nsg-id $nsg_id| jq -r '.data[] | select(."resource-id" == null)."vnic-id"')
    do
        nsg_name=$(oci network nsg get --nsg-id $nsg_id | jq -r '.data."display-name"')
        echo "Ingress & Egress rules for $nsg_name"
        echo "Source,Source_type,Protocol,MaxPort,Description"
        oci network nsg rules list --nsg-id $nsg_id --direction INGRESS | jq -r '.data[] | "\(."source"),\(."source-type"),\(."protocol"),\(."tcp-options"."destination-port-range".max),\(."description")"' 
        echo "Destination,Destination_type,Protocol,MaxPort,Description"
        oci network nsg rules list --nsg-id $nsg_id --direction EGRESS | jq -r '.data[] | "\(."destination"),\(."destination-type"),\(."protocol"),\(."tcp-options"."destination-port-range".max),\(."description")"' 
    done
done
