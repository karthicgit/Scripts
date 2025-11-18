import oci
from datetime import datetime, timedelta

config = oci.config.from_file()

tenant_id = input('Enter your tenant OCID:  ')
compartment_id = input('Enter the compartment id where instance resources will be searched: ')


# To validate the compartment id entered
def validate_compartment():
    try:
        identity_client = oci.identity.IdentityClient(config)
        get_compartment_response = identity_client.get_compartment(
            compartment_id=compartment_id).data
        print(f"The compartment entered is {get_compartment_response.name}")
    except Exception as e:
        print(f"Exception occured please check if the compartment given is valid --> {str(e)}")
        raise


def usage_report(start_time, end_time):
    try:
        usage_api_client = oci.usage_api.UsageapiClient(config)

        filter_details = oci.usage_api.models.Filter(
            operator="AND",
            dimensions=[
                oci.usage_api.models.Dimension(
                    key="compartmentId",
                    value=compartment_id
                ),
                oci.usage_api.models.Dimension(
                    key="service",
                    value="COMPUTE"
                )
            ]
        )

        request_summarized_usages_response = usage_api_client.request_summarized_usages(
            request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
                tenant_id=tenant_id,
                time_usage_started=start_time,
                time_usage_ended=end_time,
                granularity="DAILY",
                filter=filter_details,
                group_by=["resourceId"],
                compartment_depth=1,
                is_aggregate_by_time=False,
                query_type="COST"))

        usage_data = request_summarized_usages_response.data.items
        cost_data = []
        for cost in usage_data:
            res_id = cost.resource_id
            if res_id.startswith("ocid1.instance"):

                found_dict = next((d for d in search_instances() if res_id in d.values()), None)
                if found_dict is None:
                    display_name = 'N/A'
                else:
                    display_name = found_dict["name"]

                start_time = cost.time_usage_started.strftime("%Y-%m-%d")
                cost_data.append({"cost": cost.computed_amount, "id": cost.resource_id, "name": display_name,
                                  "starttime": start_time})

        return cost_data
    except Exception as e:
        print(f"Exception occured {str(e)}")


def search_instances():
    search_client = oci.resource_search.ResourceSearchClient(config)
    query = f"query Instance resources where (compartmentId='{compartment_id}')"
    search_details = oci.resource_search.models.StructuredSearchDetails(
        query=query,
        type="Structured",
    )

    response = search_client.search_resources(search_details).data.items
    search_output = []
    for i in response:
        search_output.append({"id": i.identifier, "name": i.display_name})
    return search_output


if __name__ == "__main__":
    validate_compartment()

    now = datetime.now().replace(microsecond=0, second=0, minute=0, hour=0).isoformat('T', 'milliseconds') + 'Z'

    x_daysbefore = datetime.now().replace(microsecond=0, second=0, minute=0, hour=0) - timedelta(days=30)
    x_daysbefore = x_daysbefore.isoformat('T', 'milliseconds') + 'Z'

    print(usage_report(x_daysbefore, now))
