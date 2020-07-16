#Usage: python syntheticdatatoLA.py
#Author: karthic.ravindran@oracle.com
#Python version >= 3.6 

import requests
import datetime
import json
import collections
import sys
import logging
from http.client import HTTPConnection

#For DEBUG
#HTTPConnection.debuglevel = 1

username = ""
password = ""
#ex:omcurl="omctenant-tenant.omc.ocp.oraclecloud.com"  without https at the beginning
omcurl=""

#Headers - Mention the logSourceName available in LA in the header, filename and uploadName can be given any name.
Headers = {"Content-Type": "application/octet-stream","X-USER-DEFINED-PROPERTIES": "filename:synthetic,uploadName:Synthetic,logSourceName:Synthetic"}

#You can choose to collect daily or weekly by changing the timedelta
until = datetime.datetime.now() - datetime.timedelta(days=1)
untilz = until.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
since = until - datetime.timedelta(days=7)
sincez = since.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


#Fetch meId of first Synthetic Test.
testidurl="https://%s/serviceapi/apm.dataserver/api/v1/synthetic/tests?since=%s&until=%s" % (omcurl,sincez,untilz)
r=requests.get(testidurl,auth=(username,password))
data=r.json()

json_str = json.dumps(data)
resp = json.loads(json_str)
meId=resp['items'][0]['meId']

#Fetch Synthetic Test timeseries metrics with 1 hour aggregation
syntheticurl="https://%s/serviceapi/apm.dataserver/api/v1/synthetic/tests/%s/timeSeries?aggregationPeriod=60&since=%s&until=%s" % (omcurl,meId,sincez,untilz)
r=requests.get(syntheticurl,auth=(username,password))
data=r.json()

#Metrics
averageResponseTime=json.loads(json.dumps(data['averageResponseTime']))
avgTotalContentLoadTime=json.loads(json.dumps(data['avgTotalContentLoadTime']))
avgTotalLoadTime=json.loads(json.dumps(data['avgTotalLoadTime']))
avgTotalWaitTime=json.loads(json.dumps(data['avgTotalWaitTime']))
avgConnectTime=json.loads(json.dumps(data['avgConnectTime']))
avgFirstByteTime=json.loads(json.dumps(data['avgFirstByteTime']))
avgRedirectTime=json.loads(json.dumps(data['avgRedirectTime']))
avgTransferRate=json.loads(json.dumps(data['avgTransferRate']))
avgDownloadSize=json.loads(json.dumps(data['avgDownloadSize']))
ajaxCallCount=json.loads(json.dumps(data['ajaxCallCount']))
failureCount=json.loads(json.dumps(data['failureCount']))
totalTime=json.loads(json.dumps(data['totalTime']))
minResponseTime=json.loads(json.dumps(data['minResponseTime']))
maxResponseTime=json.loads(json.dumps(data['maxResponseTime']))
totalTime=json.loads(json.dumps(data['totalTime']))
formattedTime=json.loads(json.dumps(data['formattedTime']))

#Build json compatible with LA json parser.
def buildjson(n):
      d = collections.OrderedDict()
      d['averageResponseTime'] = averageResponseTime[n]
      d['avgTotalContentLoadTime'] = avgTotalContentLoadTime[n]
      d['avgTotalLoadTime'] = avgTotalLoadTime[n]
      d['avgTotalWaitTime'] = avgTotalWaitTime[n]
      d['avgConnectTime'] = avgConnectTime[n]
      d['avgFirstByteTime'] = avgFirstByteTime[n]
      d['avgRedirectTime'] = avgRedirectTime[n]
      d['avgTransferRate'] = avgTransferRate[n]
      d['avgDownloadSize'] = avgDownloadSize[n]
      d['ajaxCallCount'] = ajaxCallCount[n]
      d['failureCount'] = failureCount[n]
      d['totalTime'] = totalTime[n]
      d['minResponseTime'] = minResponseTime[n]
      d['maxResponseTime'] = maxResponseTime[n]
      d['formattedTime'] = formattedTime[n]
      return d

jsondata=json.dumps([buildjson(n) for n in range(len(averageResponseTime))])


#Upload to LA
url="https://%s/serviceapi/loganalytics/logFilesReceiver/upload" % (omcurl)
logreq = requests.post(url, data=jsondata,headers=Headers,auth=(username,password))

