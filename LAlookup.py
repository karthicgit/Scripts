import oci
import os
import sys
config = oci.config.from_file("<configfile_path>")

if len(sys.argv != 2):
    print(f"Number of argument is wrong ex: python3 <filename> <lookupfile_directory_path>")
    exit(1)

log_analytics_client = oci.log_analytics.LogAnalyticsClient(config)
object_storage_client = oci.object_storage.ObjectStorageClient(config)

namespace = object_storage_client.get_namespace().data
lookup_type="Lookup"
path = sys.argv[1]
os.chdir(path)
try:
    lookup_files = [x for x in os.listdir(path) if x.endswith('.csv')]
    for f in lookup_files:
        if os.stat(f).st_size < 10485760:
            register_lookup_response = log_analytics_client.register_lookup(
                namespace_name=namespace,
                type=lookup_type,
                register_lookup_content_file_body=open(f,"rb").read(),
                name=os.path.splitext(f)[0],
                description="Imported Lookup",
                is_hidden=False)
        else:
            print(f"File:{f} size greater than 10MB")
except Exception as e1:
    print(e1)
