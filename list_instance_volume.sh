#!/bin/bash
compartment_id=<placeholder for compartment OCID>
echo "#######Block Volume & Boot Volume details attached to an instance##########"
echo "Name,Size,TimeCreated,State,AutoTune,Availability_Domain,VPU"
for instance_id in $(oci compute instance list -c $compartment_id| jq -r '.data[].id')
do
    instance_name=$(oci compute instance get --instance-id $instance_id | jq -r '.data."display-name"')
    
    for volume_id in $(oci compute volume-attachment list -c $compartment_id --instance-id $instance_id|jq -r '.data[]."volume-id"')
    do
        echo "Instance name is $instance_name"
        oci bv volume get --volume-id $volume_id | jq -r '.data |"\(."display-name"),\(."size-in-gbs"),\(."time-created"),\(."lifecycle-state"),\(."is-auto-tune-enabled"),\(."availability-domain"),\(."vpus-per-gb")"' 
    done
done
#list boot volumes attached. Generally the name of the instance and the boot volume will be similar.
ADS=$(oci iam availability-domain list |jq -r '.data[]| .name')
for AD in $ADS
do
    for boot_volume_id in $(oci compute boot-volume-attachment list --availability-domain $AD --compartment-id $compartment_id | jq -r '.data[]."boot-volume-id"')
    do
        oci bv boot-volume get --boot-volume-id $boot_volume_id | jq -r '.data |"\(."display-name"),\(."size-in-gbs"),\(."time-created"),\(."lifecycle-state"),\(."is-auto-tune-enabled"),\(."availability-domain"),\(."vpus-per-gb")"'
    done
done
