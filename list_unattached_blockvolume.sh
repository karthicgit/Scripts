#!/bin/bash
region=<region>
tenancy_id=<tenancy_ocid>
for compartment_id in `oci iam compartment list -c $tenancy_id --lifecycle-state ACTIVE --compartment-id-in-subtree true --all|jq -r '.data[]|.id'`;
do  
    bv_id=`oci bv volume list --compartment-id $compartment_id  --region $region --lifecycle-state AVAILABLE|  grep '"id"' | cut -d '"' -f 4`
    if [[ -z "$bv_id" ]];
    then
        echo "No BlockVolumes in this compartment skipping"
        continue
    else
        oci bv volume list --compartment-id $compartment_id  --region $region --lifecycle-state AVAILABLE|  grep '"id"' | cut -d '"' -f 4 > all_volumes
        oci compute volume-attachment list --compartment-id $compartment_id --region $region | grep '"volume-id"' | cut -d'"' -f 4 > attached_volumes  #get attached volumes and place them in a file
    fi
    for volumes in $(grep -vxFf attached_volumes all_volumes ); 
    do
        if [[ "$volumes" == ocid1.volume.* ]]; 
        then 
            oci bv volume get --volume-id $volumes | jq -r '.data |"\(."display-name"),\(."size-in-gbs"),\(."time-created"),\(."lifecycle-state"),\(."is-auto-tune-enabled"),\(."availability-domain"),\(."vpus-per-gb")"' >> UNATTACHED_VOLUME_DETAILS
        fi
    done
done
