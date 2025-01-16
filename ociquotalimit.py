import concurrent.futures
import oci
import json
import sys

#By default it expects the config to be present in ~/.oci/config.Specify the absolute path if its in  a different path.
config = oci.config.from_file()
tenancy_id = config['tenancy']

#Replace the placeholder with correct values
log_group_id = "<LA_log_group_ocid>"
LA_NAMESPACE = "<Logging analytics namespace>"

limits_client = oci.limits.LimitsClient(config)
identity_client = oci.identity.IdentityClient(config)
log_analytics_client = oci.log_analytics.LogAnalyticsClient(config)
quotas_client = oci.limits.QuotasClient(config)

# custom_retry_strategy = oci.retry.RetryStrategyBuilder(
#     # Make up to 5 service calls
#     max_attempts_check=True,
#     max_attempts=5,
#     # Don't exceed a total of 300 seconds for all service calls
#     total_elapsed_time_check=True,
#     total_elapsed_time_seconds=300
# ).get_retry_strategy()

#Fetch availability domain names
availability_domains = identity_client.list_availability_domains(compartment_id=tenancy_id).data
availability_domain_name = []
for ad in availability_domains:
    availability_domain_name.append(ad.name)


#To fetch limit_name,service_name and scope details from limit_definitions API
def list_services() -> dict:
    list_limit_definitions_response = oci.pagination.list_call_get_all_results(limits_client.list_limit_definitions,
                                                                               compartment_id=tenancy_id)
    limit_list = {}
    for i in list_limit_definitions_response.data:
        if i.are_quotas_supported and not i.is_deprecated and i.is_resource_availability_supported:
            service_name = i.service_name
            limit_name = i.name
            scope = i.scope_type
            limit_dict = {f"{limit_name}_{service_name}": scope}
            limit_list.update(limit_dict)

    return limit_list

#Function to fetch the compartment name from the quota statements.It can handle below example statements.If you have a different testcase please modify.
#Example1: set quota <servicename> <limitname> to <number> in compartment <compartmentname>
#Example2: set quota <servicename> <limitname> to <number> in compartment <parentcompartmentname>:<childcompartmentname>
#Example3: set quota <servicename> <limitname> to <number> in compartment <compartmentname> where <statements>
def get_string_after_last_colon(input_string):
    if ':' in input_string:
        parts = input_string.rsplit(':', 1)  # Split from the right, only once
        if len(parts) > 1:
            end_string=parts[1].strip()
            return end_string.split()[0]
    elif ":" not in input_string:
        index = input_string.find("compartment")
        if index != -1:
            # Slice the string from the end of "compartment"
            substring = input_string[index + len("compartment"):].strip()
            
            # Split the substring by whitespace and return the first part
            first_string = substring.split()[0] if substring else None
            return first_string
    else:
        return None


#To list compartment names from the quota policy statements
def list_quota_compartment() -> list:
    list_quotas_response = quotas_client.list_quotas(
        compartment_id=tenancy_id,
        lifecycle_state="ACTIVE",
        sort_order="ASC",
        sort_by="NAME")
    compartment_name_list = []
    for i in list_quotas_response.data:
        quota_id = i.id
        get_quota_response = quotas_client.get_quota(
            quota_id=quota_id)
        for statement in get_quota_response.data.statements:
            if "compartment" in statement:
                compartment = get_string_after_last_colon(statement)
                if compartment is not None:
                    compartment_name_list.append(compartment)
    print(set(compartment_name_list))
    return list(set(compartment_name_list))


#To upload data to logging analytics
def upload_to_logginganalytics(data):
    log_analytics_client.upload_log_file(
        namespace_name=LA_NAMESPACE,
        upload_name="Service_Quota",
        log_source_name="Quota",
        opc_meta_loggrpid=log_group_id,
        filename="quota.json",
        content_type="application/octet-stream",
        upload_log_file_body=data)


#To get compartment_ocid from compartment_name.
def list_compartment_id(compartment_name) -> str:
    compartment_ocid = oci.pagination.list_call_get_all_results(identity_client.list_compartments,
                                                                compartment_id=tenancy_id,
                                                                access_level="ACCESSIBLE",
                                                                compartment_id_in_subtree=True,
                                                                sort_order="ASC",
                                                                name=compartment_name,
                                                                lifecycle_state="ACTIVE").data[0].id
    return compartment_ocid


def list_compartments_quota(compartment_name):
    all_quota = []
    compartment_id = list_compartment_id(compartment_name)
    print(compartment_id)
    for name, scope in list_services().items():
        limit_name = name.split('_')[0]
        service_name = name.split('_')[1]
        if scope == "AD":
            for ad_name in availability_domain_name:
                get_resource_availability_response = limits_client.get_resource_availability(
                    service_name=service_name,
                    limit_name=limit_name,
                    availability_domain=ad_name,
                    compartment_id=compartment_id)
                resource_availability_tmp = get_resource_availability_response.data
                if resource_availability_tmp.effective_quota_value is not None and int(
                        resource_availability_tmp.available) != 0:
                    used = resource_availability_tmp.used
                    available = resource_availability_tmp.available
                    quota_value = resource_availability_tmp.effective_quota_value
                    quota_dict = {"Used": used, "Available": available, "Quota": quota_value, "Limit": limit_name,
                                  "Service": service_name, "Compartment": compartment_name, "AD": ad_name}
                    all_quota.append(quota_dict)
        else:
            get_resource_availability_response = limits_client.get_resource_availability(
                service_name=service_name,
                limit_name=limit_name,
                compartment_id=compartment_id)
            resource_availability_tmp = get_resource_availability_response.data
            if resource_availability_tmp.effective_quota_value is not None and int(
                    resource_availability_tmp.available) != 0:
                used = resource_availability_tmp.used
                available = resource_availability_tmp.available
                quota_value = resource_availability_tmp.effective_quota_value
                quota_dict = {"Used": used, "Available": available, "Quota": quota_value, "Limit": limit_name,
                              "Service": service_name, "Compartment": compartment_name}
                all_quota.append(quota_dict)

    print(f"Size of the data:{sys.getsizeof(all_quota)}")
    upload_data = json.dumps(all_quota)
    upload_to_logginganalytics(upload_data)


if __name__ == '__main__':
    compartment_names = list_quota_compartment()
    # This check is there if the quota policy statement is written as compartment <rootcompartmentname>. Substitute the root tenancy name in the below if statement
    if "<tenancy_name>" in compartment_names:
        compartment_names.remove('<tenancy_name>')
    print(compartment_names)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(list_compartments_quota, compartment_names)
