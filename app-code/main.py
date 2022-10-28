"""
CISCO SAMPLE CODE LICENSE
                                  Version 1.1
                Copyright (c) 2020 Cisco and/or its affiliates

   These terms govern this Cisco Systems, Inc. ("Cisco"), example or demo
   source code and its associated documentation (together, the "Sample
   Code"). By downloading, copying, modifying, compiling, or redistributing
   the Sample Code, you accept and agree to be bound by the following terms
   and conditions (the "License"). If you are accepting the License on
   behalf of an entity, you represent that you have the authority to do so
   (either you or the entity, "you"). Sample Code is not supported by Cisco
   TAC and is not tested for quality or performance. This is your only
   license to the Sample Code and all rights not expressly granted are
   reserved.

   1. LICENSE GRANT: Subject to the terms and conditions of this License,
      Cisco hereby grants to you a perpetual, worldwide, non-exclusive, non-
      transferable, non-sublicensable, royalty-free license to copy and
      modify the Sample Code in source code form, and compile and
      redistribute the Sample Code in binary/object code or other executable
      forms, in whole or in part, solely for use with Cisco products and
      services. For interpreted languages like Java and Python, the
      executable form of the software may include source code and
      compilation is not required.

   2. CONDITIONS: You shall not use the Sample Code independent of, or to
      replicate or compete with, a Cisco product or service. Cisco products
      and services are licensed under their own separate terms and you shall
      not use the Sample Code in any way that violates or is inconsistent
      with those terms (for more information, please visit:
      www.cisco.com/go/terms).

   3. OWNERSHIP: Cisco retains sole and exclusive ownership of the Sample
      Code, including all intellectual property rights therein, except with
      respect to any third-party material that may be used in or by the
      Sample Code. Any such third-party material is licensed under its own
      separate terms (such as an open source license) and all use must be in
      full accordance with the applicable license. This License does not
      grant you permission to use any trade names, trademarks, service
      marks, or product names of Cisco. If you provide any feedback to Cisco
      regarding the Sample Code, you agree that Cisco, its partners, and its
      customers shall be free to use and incorporate such feedback into the
      Sample Code, and Cisco products and services, for any purpose, and
      without restriction, payment, or additional consideration of any kind.
      If you initiate or participate in any litigation against Cisco, its
      partners, or its customers (including cross-claims and counter-claims)
      alleging that the Sample Code and/or its use infringe any patent,
      copyright, or other intellectual property right, then all rights
      granted to you under this License shall terminate immediately without
      notice.

   4. LIMITATION OF LIABILITY: CISCO SHALL HAVE NO LIABILITY IN CONNECTION
      WITH OR RELATING TO THIS LICENSE OR USE OF THE SAMPLE CODE, FOR
      DAMAGES OF ANY KIND, INCLUDING BUT NOT LIMITED TO DIRECT, INCIDENTAL,
      AND CONSEQUENTIAL DAMAGES, OR FOR ANY LOSS OF USE, DATA, INFORMATION,
      PROFITS, BUSINESS, OR GOODWILL, HOWEVER CAUSED, EVEN IF ADVISED OF THE
      POSSIBILITY OF SUCH DAMAGES.

   5. DISCLAIMER OF WARRANTY: SAMPLE CODE IS INTENDED FOR EXAMPLE PURPOSES
      ONLY AND IS PROVIDED BY CISCO "AS IS" WITH ALL FAULTS AND WITHOUT
      WARRANTY OR SUPPORT OF ANY KIND. TO THE MAXIMUM EXTENT PERMITTED BY
      LAW, ALL EXPRESS AND IMPLIED CONDITIONS, REPRESENTATIONS, AND
      WARRANTIES INCLUDING, WITHOUT LIMITATION, ANY IMPLIED WARRANTY OR
      CONDITION OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-
      INFRINGEMENT, SATISFACTORY QUALITY, NON-INTERFERENCE, AND ACCURACY,
      ARE HEREBY EXCLUDED AND EXPRESSLY DISCLAIMED BY CISCO. CISCO DOES NOT
      WARRANT THAT THE SAMPLE CODE IS SUITABLE FOR PRODUCTION OR COMMERCIAL
      USE, WILL OPERATE PROPERLY, IS ACCURATE OR COMPLETE, OR IS WITHOUT
      ERROR OR DEFECT.

   6. GENERAL: This License shall be governed by and interpreted in
      accordance with the laws of the State of California, excluding its
      conflict of laws provisions. You agree to comply with all applicable
      United States export laws, rules, and regulations. If any provision of
      this License is judged illegal, invalid, or otherwise unenforceable,
      that provision shall be severed and the rest of the License shall
      remain in full force and effect. No failure by Cisco to enforce any of
      its rights related to the Sample Code or to a breach of this License
      in a particular situation will act as a waiver of such rights. In the
      event of any inconsistencies with any other terms, this License shall
      take precedence.
"""

import os
import time
from datetime import datetime, timedelta
from tracemalloc import start

import dnacentersdk
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import requests
import urllib3
urllib3.disable_warnings() 
import json

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.write_api import WritePrecision

# Get configuration data.
load_dotenv()

dnacenter_sandbox_url = os.getenv('DNACENTER_SANDBOX_URL')
dnacenter_sandbox_user = os.getenv('DNACENTER_SANDBOX_USER')
dnacenter_sandbox_password = os.getenv('DNACENTER_SANDBOX_PASSWORD')

influxdb_host = os.getenv('INFLUX_HOST')
influxdb_port = os.getenv('INFLUX_PORT')
influxdb_username = os.getenv('INFLUX_USERNAME')
influxdb_password = os.getenv('INFLUX_PASSWORD')
influxdb_dnabucket = os.getenv('INFLUX_DNACBUCKET')
influxdb_token = os.getenv('INFLUX_TOKEN')
influxdb_org = os.getenv('INFLUX_ORG')
sleep_interval = int(os.getenv('SLEEP_INTERVAL'))

print(f"INFLUX DB HOST: {influxdb_host}")

client = InfluxDBClient(url=f"http://{influxdb_host}:8086", token=influxdb_token, org=influxdb_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Setup DNA Center Sandbox.
dnacenter_sandbox = dnacentersdk.DNACenterAPI(
    base_url=dnacenter_sandbox_url,
    username=dnacenter_sandbox_user,
    password=dnacenter_sandbox_password,
    verify=False)

# Set up session
session = requests.Session()

# Helper functions
def post_login_credentials():
    global cookies
    print("*** Posting the login credentials to the dashboard ***")
    url = f"{dnacenter_sandbox_url}/api/system/v1/auth/login"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    body = {
        'username': dnacenter_sandbox_user,
        'passphrase': dnacenter_sandbox_password
    }
    response = session.post(url, data=body, headers=headers, verify=False)
    # print(response.headers)
    cookies_header = response.headers['Set-Cookie']
    # print(cookies_header)
    cookies = cookies_header.split(";")[0]
    # print(response)
    # print(response.text)
    if response.ok:
        print("*** The login credentials were successfully posted ***") 

##### COLLECTOR FUNCTIONS #####

def get_application_info():
    start_time, end_time = get_timestamps()
    sites = dnacenter_sandbox.sites.get_site().response
    for site in sites:
        url = f"{dnacenter_sandbox_url}/api/assurance/v1/application/health-trend?startTime={start_time}&endTime={end_time}&fetchLowHealthApp=true&siteId={site.id}&timeLabel=3%20hours"
        headers={
            'Content-Type': 'application/json',
            'Cookie': cookies
        }
        response = session.get(url, headers=headers)

        healthy_apps = response.json()['response']['trend']
        
        if len(healthy_apps) > 0:
            healthy_apps_percent = healthy_apps[-1]['healthyAppsPercent']
            if healthy_apps_percent == 'null' or not healthy_apps_percent:
                healthy_apps_percent = 0
            else: 
                healthy_apps_percent = int(healthy_apps_percent)
            name = site.name.replace(' ','_')
            data = f"application_info,site_id={site.id},site_name={name} healthy_apps_percent={healthy_apps_percent}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)

        apps = dnacenter_sandbox.applications.applications(site_id=site.id)
        for app in apps['response']:
            traffic = app['usageBytes']
            data = f"application_traffic,app_name={app['name']}" + ",site_name=" + \
                site['name'].lstrip(' ').replace(" ", "_") + " traffic=" + str(traffic)
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)

def get_wireless_latency(start_time, end_time):
    url = f'{dnacenter_sandbox_url}/api/assurance/v1/network-device/radioAnalytics?type=latencyByClcnt&startTime={start_time}&endTime={end_time}'
    response = session.get(url)
    headers={
        'Content-Type': 'application/json',
        'Cookie': cookies
    }
    response = session.get(url, headers=headers)

def get_timestamps():
    now = datetime.now()
    delta = timedelta(days=1)
    yesterday = now - delta
    now_epochs = int(now.timestamp() * 1000)
    yesterday_epochs = int(yesterday.timestamp() * 1000)
    return yesterday_epochs, now_epochs

def get_device_health():
    sites = dnacenter_sandbox.sites.get_site().response
    for site in sites:
        devices = dnacenter_sandbox.sites.get_membership(site['id'], device_family="Switches and Hubs").device
        for device in devices:
            for r in device.response:
                device_details = dnacenter_sandbox. \
                    devices.get_device_detail(identifier="uuid",
                                                search_by=r.instanceUuid).response

                device_health = device_details.overallHealth
                device_name = r.hostname
                data = f"device_health,site_name=" + \
                        site['name'].lstrip(' ').replace(" ", "_") + f",device_name={device_name} device_health=" + str(device_health)
                client = InfluxDBClient(url=f"http://{influxdb_host}:8086", token=influxdb_token, org=influxdb_org)
                write_api = client.write_api(write_options=SYNCHRONOUS)
                write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
    print("Successfully wrote device health data")

def get_site_health():
    sites = dnacenter_sandbox.sites.get_site_health().response
    for site in sites:
        site_health = site.networkHealthAverage
        site_name = site.siteName
        site_id = site.siteId
        # print(json.dumps(site, indent=2))
        if site_health is not None:
            data = "site_health,host=" + site_id + ",site_name=" + \
                site_name.lstrip(' ').replace(" ", "_") + " site_health=" + str(site_health)
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
    print("Successfully wrote site health data")

def get_client_count():
    client_health = dnacenter_sandbox.clients.get_overall_client_health()
    
    # Client count
    clients = client_health.response[0].scoreDetail
    client_count = 0
    for client in clients:
        client_count = client_count + client.clientCount
    data = "clients_count,client=p1 clients=" + str(client_count)
    write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)

    # Client health
    for client in clients:
        data = None
        if client['scoreCategory']['value'] == 'ALL':
            data = "clients_health,type=all count=" + str(client['clientCount'])
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 
            data = "clients_health,type=all unique=" + str(client['clientUniqueCount'])
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 
        elif client['scoreCategory']['value'] == 'WIRED':
            data = "clients_health,type=wired count=" + str(client['clientCount'])
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 
            data = "clients_health,type=wired unique=" + str(client['clientUniqueCount'])
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 
        elif client['scoreCategory']['value'] == 'WIRELESS':
            data = "clients_health,type=wireless count=" + str(client['clientCount'])
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 
            data = "clients_health,type=wireless unique=" + str(client['clientUniqueCount'])
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 
        if data is not None:
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 
    
    get_client_frequencies()

    # Client health per site
    sites = dnacenter_sandbox.sites.get_site()
    start_time, end_time = get_timestamps()
    for site in sites.response:
        payload = {
            "type": "SITE",
            "filters": {
                "ssid": [],
                "frequency": ""
            },
            "startTime": start_time,
            "endTime": end_time,
            "originalEndTime": end_time,
            "typeIdList": [
                site['siteHierarchy']
            ],
            "currentTime": end_time,
            "timeAPITime": end_time
        }
        url = f"{dnacenter_sandbox_url}/api/assurance/v1/host/dash/healthtrendline"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': cookies
        }
        trends = session.post(url, headers=headers, json=payload).json()['response']
        for trend in trends:
            trend_name = trend['type']
            trend_last_value = trend['values'][0]['value']
            trend_auth_fail = trend['values'][0]['aaa_fail_cnt']
            trend_dhcp_fail = trend['values'][0]['dhcp_fail_cnt']
            trend_assoc_fail = trend['values'][0]['assoc_fail_cnt']
            trend_other_fail = trend['values'][0]['other_fail_cnt']
            if trend_auth_fail is None:
                trend_auth_fail = 0
            if trend_dhcp_fail is None:
                trend_dhcp_fail = 0
            if trend_assoc_fail is None:
                trend_assoc_fail = 0 
            if trend_other_fail is None:
                trend_other_fail = 0 
            data = f"clients_health,type={trend_name}" + ",site_name=" + \
                site['name'].lstrip(' ').replace(" ", "_") + " health=" + str(trend_last_value)
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
            data = f"service_health,service=auth_fail,site_name=" + site['name'].lstrip(' ').replace(" ", "_") + f" count={trend_auth_fail}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
            data = f"service_health,service=dhcp_fail,site_name=" + site['name'].lstrip(' ').replace(" ", "_") + f" count={trend_dhcp_fail}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
            data = f"service_health,service=assoc_fail,site_name=" + site['name'].lstrip(' ').replace(" ", "_") + f" count={trend_assoc_fail}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
            data = f"service_health,service=other_fail,site_name=" + site['name'].lstrip(' ').replace(" ", "_") + f" count={trend_other_fail}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
    
    # Client count per site
    for site in sites.response:
        payload = {
            "typeList": {
                "type": "SITE",
                "typeIdList": [],
                "startTime": start_time,
                "endTime": end_time,
                "filters": {
                    "ssid": [],
                    "frequency": ""
                },
                "currentTime": end_time,
                "timeAPITime": end_time
            },
            "option": "CLIENT",
            "selectedTypeIdList": [
                site['siteHierarchy']
            ]
        }
        url = f"{dnacenter_sandbox_url}/api/assurance/v1/host/dash/healthdetail"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': cookies
        }
        client_counts = session.post(url, headers=headers, json=payload).json()['response']
        for score in client_counts[0]['scoreDetail']:
            client_type = score['scoreCategory']['value']
            client_count_value = score['clientCount']
            client_unique_count = score['clientUniqueCount']
            data = f"clients_health,type={client_type},site_name=" + site['name'].lstrip(' ').replace(" ", "_") + f" count={client_count_value}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
            data = f"clients_health,type={client_type},site_name=" + site['name'].lstrip(' ').replace(" ", "_") + f" unique={client_unique_count}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)


    # Clients per SSID
    url = f"{dnacenter_sandbox_url}/api/assurance/v1/host"
    headers = {
            'Content-Type': 'application/json',
            'Cookie': cookies
        }
    body = {
        "typeList": {
            "type": "SITE",
            "typeIdList": [],
            "startTime": start_time,
            "endTime": end_time,
            "filters": {
                "ssid": [],
                "frequency": ""
            },
            "currentTime": end_time,
            "timeAPITime": end_time
        },
        "option": "CLIENT",
        "selectedTypeIdList": []
    }
    clients = session.post(url, headers=headers, verify=False, json=body).json()['response']
    ssids = {}
    for client in clients:
        ssid = client['ssid']
        if ssid is not None:
            if ssid in ssids:
                ssids[ssid] += 1
            else:
                ssids[ssid] = 1
    for ssid in ssids:
        data = f"ssid_count,ssid_name=" + ssid.lstrip(' ').replace(" ", "_") + f" count={ssids[ssid]}"
        write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)

def get_client_frequencies():
    start_time, end_time = get_timestamps()
    url = f'{dnacenter_sandbox_url}/api/assurance/v1/host?startTime={start_time}&endTime={end_time}'
    headers={
        'Content-Type': 'application/json',
        'Cookie': cookies
    }
    body = {
        "typeList": {
            "type": "WIRELESS",
            "typeIdList": [],
            "startTime": int(start_time),
            "endTime": int(end_time),
            "filters": {
                "ssid": [],
                "frequency": ""
            },
            "currentTime": int(end_time),
            "timeAPITime": int(end_time)
        },
        "option": "CLIENT",
        "selectedTypeIdList": []
    }
    clients = session.post(url, headers=headers, json=body).json()['response']
    with open("resp.json", "w") as f:
        json.dump(clients, f, indent=2)
    
    freq_dict = {}
    for host in clients:
        if host['location'] in freq_dict:
            if host['hostType'] == "WIRELESS" and host['frequency'] in freq_dict[host['location']]:
                freq_dict[host['location']][host['frequency']] += 1
            elif host['hostType'] == "WIRELESS" and host['frequency'] is not None:
                freq_dict[host['location']][host['frequency']] = 1
        elif host['hostType'] == "WIRELESS" and host['frequency'] is not None:
            freq_dict[host['location']] = {
                host['frequency']: 1
            }
    
    for loc in freq_dict:
        for freq in freq_dict[loc]:
            data = f"client_frequency,frequency={freq},site_name=" + loc.lstrip(' ').replace(" ", "_") + f" count={freq_dict[loc][freq]}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)

def get_issue_count():
    sites = dnacenter_sandbox.sites.get_site().response
    issues = dnacenter_sandbox.issues.issues()
    data = "issue_count,type=all count=" + str(issues.totalCount)
    write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
    for site in sites:
        priority_dict = {
            'P1' : 0,
            'P2' : 0,
            'P3' : 0,
            'P4' : 0
        }
        for issue in issues['response']:
            if issue['siteId'] == site['id']:
                id = issue['issueId']
                details = dnacenter_sandbox.issues.get_issue_enrichment_details({
                    "entity_type" : "issue_id",
                    "entity_value" : id
                })
                priority = details['issueDetails']['issue'][0]['issuePriority']
                if priority in priority_dict:
                    priority_dict[priority] += 1
        for prio in priority_dict:
            data = f"issue_count,type={prio}" + ",site_name=" + \
                site['name'].lstrip(' ').replace(" ", "_") + " count=" + str(priority_dict[prio])
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data) 

def get_network_health():
    url = f"{dnacenter_sandbox_url}/dna/system/api/v1/auth/token"
    headers = {
        "Accept" : "application/json"
    }
    response = requests.post(
        url=url,
        headers=headers,
        auth=HTTPBasicAuth(dnacenter_sandbox_user, dnacenter_sandbox_password),
        verify=False
        )
    token = response.json()['Token']
    start_time, end_time = get_timestamps()
    sites = dnacenter_sandbox.sites.get_site().response
    for site in sites:
        url=f"{dnacenter_sandbox_url}/api/assurance/v1/network-device/healthSummary?measureBy=sites&windowInMin=1&startTime={start_time}&endTime={end_time}&currTime={end_time}&offset=1&approach=latest"
        headers = {
            "Accept" : "application/json",
            "X-Auth-Token" : token
        }
        payload = {
            "sites": [
                site['siteHierarchy']
            ]
        }
        response = requests.post(
            url=url,
            headers=headers,
            verify=False,
            json=payload
        )
        network_health = response.json()
        if 'response' in network_health:
            data = f"network_health,site_name=" + site['name'].lstrip(' ').replace(" ", "_") + f" network_health={network_health['response'][0]['healthScore']}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)

def get_services_info():
    url = f"{dnacenter_sandbox_url}/dna/system/api/v1/auth/token"
    headers = {
        "Accept" : "application/json"
    }
    response = requests.post(
        url=url,
        headers=headers,
        auth=HTTPBasicAuth(dnacenter_sandbox_user, dnacenter_sandbox_password),
        verify=False
        )
    token = response.json()['Token']
    url=f"{dnacenter_sandbox_url}/api/assurance/v1/networkServices"
    headers = {
        "Accept" : "application/json",
        "X-Auth-Token" : token,
        "Content-Type": "application/json"
    }
    start_time, end_time = get_timestamps()
    sites = dnacenter_sandbox.sites.get_site()
    for site in sites:
        payload = {
            "startTime": start_time,
            "endTime": end_time,
            "currentTime": start_time,
            "timeAPITime": start_time,
            "typeList": {
                "type": "SITE",
                "typeIdList": [
                    "__global__"
                ]
            },
            "serverType": "AAA",
            "apiType": [
                "TREND"
            ]
        }

        # AAA
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            verify=False
        )
        services_info = response.json()['response']['trend']
        if len(services_info) > 0:
            data = f"service_health,service=auth_success count={services_info[-1]['successfulTransactions']}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
            data = f"service_health,service=auth_fail count={services_info[-1]['failedTransactions']}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
        
        # DHCP
        payload['serverType'] = 'DHCP'
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            verify=False
        )
        services_info = response.json()['response']['trend']
        if len(services_info) > 0:
            data = f"service_health,service=dhcp_success count={services_info[-1]['successfulTransactions']}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)
            data = f"service_health,service=dhcp_fail count={services_info[-1]['failedTransactions']}"
            write_api.write(bucket=influxdb_dnabucket, org=influxdb_org, record=data)

##### COLLECTOR FUNCTIONS #####

# Log in to the dashboard GUI
post_login_credentials()

# Main loop
while True:
    get_device_health()
    get_site_health()  
    get_client_count()  
    get_issue_count()
    get_network_health()
    get_application_info()
    # get_services_info()

    print(f"*** End of loop. Now we are going to wait for {sleep_interval} seconds.")
    time.sleep(sleep_interval)
