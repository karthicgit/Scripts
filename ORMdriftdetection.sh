#!/bin/bash
#set -x
compartment_id=<placeholder for compartmentocid>
stack_list=`oci resource-manager stack list --all -c $compartment_id --lifecycle-state ACTIVE --query 'data[*].id'|grep -i ocid|tr -d '"'|tr -d ','`
final_stack_list=`echo $stack_list |tr -d "'"`
for stack in $final_stack_list
do
    oci resource-manager stack detect-drift --stack-id $stack --wait-for-state SUCCEEDED --wait-for-state FAILED --wait-interval-seconds 10
    sync_status=`oci resource-manager stack get --stack-id $stack|grep "stack-drift-status"| awk '{print $2}'|tr -d ','`
    if [ $sync_status != '"IN_SYNC"' ]
    then
        echo "Stack id ${stack} is out of sync" > ORMstackdriftreport.txt
    fi
done
