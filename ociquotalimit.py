import concurrent.futures
import oci
import json

config = oci.config.from_file()
tenancy_id = "<tenancy_ocid>"
log_group_id = "<LA_log_group_ocid>"
LA_NAMESPACE = "<logging analytics namespace>"

limits_client = oci.limits.LimitsClient(config)
identity_client = oci.identity.IdentityClient(config)
log_analytics_client = oci.log_analytics.LogAnalyticsClient(config)

availability_domains = identity_client.list_availability_domains(compartment_id=tenancy_id).data
availability_domain_name = []
for ad in availability_domains:
    availability_domain_name.append(ad.name)


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


def get_string_after_last_colon(input_string):
    if ':' in input_string and "compartment" in input_string:
        # Split the string by colon and return the last part
        return input_string.split(':')[-1].strip()
    else:
        # Check for the word 'compartment'
        if 'compartment' in input_string:
            # Split the string by 'compartment' and return the part after it
            return input_string.split('compartment')[-1].strip()
        else:
            # If neither is found, return None
            return None


def list_quota_compartment() -> list:
    quotas_client = oci.limits.QuotasClient(config)
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
                # print(statement)
                compartment = get_string_after_last_colon(statement)
                if compartment is not None:
                    compartment_name_list.append(compartment)
    print(set(compartment_name_list))
    return list(set(compartment_name_list))


def upload_to_logginganalytics(data):
    log_analytics_client.upload_log_file(
        namespace_name=LA_NAMESPACE,
        upload_name="Service_Quota",
        log_source_name="Quota",
        opc_meta_loggrpid=log_group_id,
        filename="quota.json",
        content_type="application/octet-stream",
        upload_log_file_body=data)


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
