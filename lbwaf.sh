#!/bin/bash
#set -x
usage()  
{  
echo "Usage: $0 <vcn_cidr> <subnet_cidr>"
echo "Example:" $0 "10.0.0.0/16" "10.0.1.0/24"  
echo "Example: To destroy all resources created" $0 "<vcn_cidr> <subnet_cidr> destroy"
exit 1  
} 
#read -p "Enter the region in format(eu-frankfurt-1) default is: " -e -i 'eu-frankfurt-1' region
region=`printenv OCI_REGION`
echo "Region used is $region"
read -p "Enter the compartment OCID: " -e compartment_id
read -p "Do you want to reserve IP for Loadbalancer true/false?: " -e -i 'false' reserved_ip
echo "To reserve ip is: $reserved_ip"
read -p "Enter the name for Load balancer: " -e lbname
echo "Loadbalancer name is: $lbname"

if [ $# -lt 2 ] ; then
    usage
fi
if [ ! -d "lbwaf" ]; then
    git clone https://github.com/karthicgit/ocilb.git lbwaf
fi
cd lbwaf
cp terraform.tfvars.example terraform.tfvars
terraform version
terraform init
if [ $# -eq 2 ]
then
    terraform plan -var vcn_cidrs=[\"$1\"] -var subnets={lbsubnnet={cidr_block=\"$2\"}} -var compartment_id=$compartment_id -var region=$region -var lb_options={lb1={name=\"$lbname\"\,reserved_ip=$reserved_ip}}
    echo "Do you want to do terraform apply? Y/N"
    read input
    if [ "$input" == "Y" ] || [ "$input" == "y" ]
    then
        terraform apply -auto-approve -var vcn_cidrs=[\"$1\"] -var subnets={lbsubnnet={cidr_block=\"$2\"}} -var compartment_id=$compartment_id -var region=$region -var lb_options={lb1={name=\"$lbname\"\,reserved_ip=$reserved_ip}}
    else
        exit
    fi
fi
if [ $3 == "destroy" ]; then
    terraform destroy -var vcn_cidrs=[\"$1\"] -var subnets={lbsubnnet={cidr_block=\"$2\"}} -var compartment_id=$compartment_id -var region=$region -var lb_options={lb1={name=\"$lbname\"\,reserved_ip=$reserved_ip}}
fi
