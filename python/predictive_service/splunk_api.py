
import requests
from requests.auth import HTTPBasicAuth 
import urllib3
from xml.etree import ElementTree
import pprint
import time
import datetime
import pandas as pd
from io import StringIO
import json
import subprocess
#import os

urllib3.disable_warnings()



# Usage
def get_splunk_commited_as_data():
       query="""
index="events_perf" | chart values(attributes.commited_as) over attributes.x | rename attributes.x as "Element Count" | rename values(attributes.commited_as) as "Commited_AS" 
| append [| makeresults | eval "Element Count"=500000 ] 
| append [| makeresults | eval "Element Count"=550000 ]
| append [| makeresults | eval "Element Count"=600000 ]
| fields - _time 
| sort "Element Count"
| fit StateSpaceForecast "Commited_AS" output_metadata=true holdback=0 forecast_k=3 into "app:commitas"
| rename predicted(Commited_AS) as forecast
| rename lower95(predicted(Commited_AS)) as lower95
| rename upper95(predicted(Commited_AS)) as upper95
| chart values("Commited_AS") values(lower95) values(forecast) values(upper95) BY  "Element Count"
| rename values("Commited_AS") as "Commited_AS"
| rename values(lower95) as lower95
| rename values(upper95) as upper95
| rename  values(forecast) as forecast
       """
       data=get_splunk_data(query)
       return data



def get_splunk_mem_data():
       query="""
index="events_perf" | chart values(attributes.mem) over attributes.x | rename attributes.x as "Element Count" | rename values(attributes.mem) as "Memory" 
| append [| makeresults | eval "Element Count"=500000 ] 
| append [| makeresults | eval "Element Count"=550000 ]
| append [| makeresults | eval "Element Count"=600000 ]
| fields - _time 
| sort "Element Count"
| fit StateSpaceForecast "Memory" output_metadata=true holdback=0 forecast_k=3 into "app:ordermemcon"
| rename predicted(Memory) as forecast
| rename lower95(predicted(Memory)) as lower95
| rename upper95(predicted(Memory)) as upper95
       """
       data=get_splunk_data(query)
       return data

def get_splunk_time_data():
       query="""
index="events_perf" | chart values(attributes.time) over attributes.x | rename attributes.x as "Element Count" | rename values(attributes.time) as "Time" 
| append [| makeresults | eval "Element Count"=500000 ] 
| append [| makeresults | eval "Element Count"=550000 ]
| append [| makeresults | eval "Element Count"=600000 ]
| fields - _time 
| sort "Element Count"
| fit StateSpaceForecast "Time" output_metadata=true holdback=0 forecast_k=3 into "app:ordertimecon"
| rename predicted(Time) as forecast
| rename lower95(predicted(Time)) as lower95
| rename upper95(predicted(Time)) as upper95
       """
       data=get_splunk_data(query)
       return data

def get_mem_data(length):
    global_log.info("Fetching memory data from Splunk")
    mem_df=get_splunk_mem_data()
    row=mem_df.loc[mem_df['Element Count'] == length]
    mem_data=row['forecast'].item()
    origin_mem=mem_df.loc[mem_df['Element Count'] == 0]['forecast'].item()
    diff_mem=mem_data-origin_mem
    diff_mem=diff_mem/1000
    diff_mem=float("{:.2f}".format(diff_mem))
    counter=0
    units=["bytes","kb","mb","gb"]
    while mem_data > 1000:
       mem_data=mem_data/1000
       counter+=1
    mem_data=float("{:.2f}".format(mem_data))
    unit=units[counter]
    return(str(mem_data),unit,str(diff_mem))

def get_time_data(length):
    global_log.info("Fetching time data from Splunk")
    time_df=get_splunk_time_data()
    row=time_df.loc[time_df['Element Count'] == length]
    time_data=row['forecast'].item()
    counter=0
    time_data=datetime.timedelta(seconds=time_data)
    return(time_data)

    #units=["bytes","kb","mb","gb"]
    #while mem_data > 1000:
    #   mem_data=mem_data/1000
    #   counter+=1
    #mem_data=float("{:.2f}".format(mem_data))
    #unit=units[counter]
    #return(str(mem_data),unit)

def get_commited_as_data(length):
    global_log.info("Fetching Commited_AS data from Splunk")
    as_df=get_splunk_commited_as_data()
    row=as_df.loc[as_df['Element Count'] == length]
    as_data=row['forecast'].item()
    return(as_data)



def get_action(diff_mem_data,time_data,commited_as_data):
    mem=subprocess.run(['cat', '/proc/meminfo'], stdout=subprocess.PIPE).stdout.decode("utf-8")
    mem_free_kb=int(mem.split("\n")[1].split("MemFree:")[1].split("kB")[0].strip())
    mem_total_kb=int(mem.split("\n")[0].split("MemTotal:")[1].split("kB")[0].strip())
    #mem_total_kb=0.0
    commited_limit=int(mem.split("\n")[33].split("CommitLimit:")[1].split("kB")[0].strip())
    oom_mode=int(subprocess.run(['cat', '/proc/sys/vm/overcommit_memory'], stdout=subprocess.PIPE).stdout.decode("utf-8"))

    mem_dec=True
    commited_dec=True
    if (float(mem_free_kb) + float(diff_mem_data))  > (float(mem_total_kb) * 0.9):
      mem_dec=False
      global_log.error("Memory(RSS) consumption close to the MemFree")
    if oom_mode==2:
      if (float(commited_as_data))  > (float(commited_limit)):
         commited_dec=False
         global_log.error("Commited_AS over CommitLimit")
    else:
      global_log.info("Evaluation will based on RSS. Ignore OOM Action due to overcommit_memory is: "+str(oom_mode))
    if not mem_dec or not commited_dec:
       return ("Abort",float(mem_total_kb) * 0.9,mem_total_kb,commited_limit,mem_dec,commited_dec)
    else:
       return ("Proceed",float(mem_total_kb) * 0.9,mem_total_kb,commited_limit,mem_dec,commited_dec)


def forecast(length,log):
    global global_log
    global_log=log
    global_log.info("***Start Splunk Forecasting***")
    mem_data=get_mem_data(length)
    time_data=get_time_data(length)
    commited_as_data=get_commited_as_data(length)
    (action,mem_free_kb,mem_total_kb,commited_limit,mem_dec,commited_dec)=get_action(mem_data[2],time_data,commited_as_data)
    global_log.info(f'Expect time consumption {time_data}, RSS/Memory Limit: {mem_data[0]}{mem_data[1]}/{mem_free_kb}{mem_data[1]}, Commited_AS/CommitLimit: {commited_as_data}/{commited_limit}, Recommended Action: {action}')
    if action=="Abort":
       if not mem_dec:
          raise Exception(f'Abort the service execution due to RSS close to the Memory Limit')
       elif not commited_dec:
          raise Exception(f'Abort the service execution due to Potential OOM risk')
       else:
          raise Exception(f'Abort the service execution due to Unknow Decision from Splunk ML Enginer')
       return False
    else:
       return True


# Toolset
def get_splunk_data(query):
       #print(os.getcwd())
       global splunk_ip
       with open('packages/predictive_service/python/predictive_service/config/splunk_config.json') as f:
       #with open('config/splunk_config.json') as f:
           d = json.load(f)
           user=d["user"]
           password=d["pass"]
           max_retry=d["max_retry"]
           splunk_ip=d["splunk_ip"]
       global_log.info("Contacting Splunk Datastore: "+splunk_ip)
       #Create a search job
       sid=splunk_create_job(user,password,query)
       global_log.info("Creating job with sid: " + sid)
       #Check status of a search
       data=splunk_get_result(user,password,sid,max_retry)
       #datetime.timedelta(seconds=output)
       df_method1 = pd.read_csv(StringIO(data.decode("utf-8")))
       #print(df_method1)
       return df_method1

def splunk_create_job(user,password,query):
        response = requests.post(splunk_ip+"/services/search/jobs/",  auth = HTTPBasicAuth(user,password), data = {"search": "search "+query}, verify=False)
        #print(response.content)
        if response.status_code >= 200 and response.status_code < 300:
            root = ElementTree.fromstring(response.content)
            sid=root[0].text
        else:
            raise Exception("HTTP Response Error on splunk_create_job:"+ response.status_code)
        return sid

def splunk_check_status(user,password,sid):
        query=""
        response = requests.get(splunk_ip+"/services/search/jobs/"+sid,  auth = HTTPBasicAuth(user,password) ,verify=False)
        if response.status_code < 200 or response.status_code > 300:
            raise Exception("HTTP Response Error on splunk_check_status:"+ response.status_code)
        return response.content

def splunk_get_result(user,password,sid, max_retry):
       output=""
       retry_counter=0
       while len(output) ==  0 and retry_counter < max_retry:
           time.sleep(5)
           response = requests.get(splunk_ip+"/services/search/jobs/"+sid+"/results/",  auth = HTTPBasicAuth(user,password), data = {"output_mode": "csv"}, verify=False)
           if response.status_code >= 200 and response.status_code < 300:
                  output=response.content
           else:
                  raise Exception("HTTP Response Error on splunk_get_result:"+ response.status_code)
           retry_counter+=1
       return output

