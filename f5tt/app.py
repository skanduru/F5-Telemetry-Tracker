#!/usr/bin/python3

from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse,StreamingResponse
import os
import sys
import ssl
import json
import uvicorn
import sched, time, datetime
import requests
import time
import threading
import smtplib
import mimetypes
import urllib3.exceptions
import base64
import gzip
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from email.message import EmailMessage

# All modules
import bigiq
import nc
import nim
import nms

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = FastAPI()

nc_mode = os.environ['DATAPLANE_TYPE']
nc_fqdn = os.environ['DATAPLANE_FQDN']
nc_user = os.environ['DATAPLANE_USERNAME']
nc_pass = os.environ['DATAPLANE_PASSWORD']
proxyDict = {}

# Scheduler for automated statistics push / call home
def scheduledPush(url, username, password, interval, pushmode):
    counter = 0

    pushgatewayUrl = url + "/metrics/job/f5tt"

    while counter >= 0:
        try:
            if nc_mode == 'NGINX_CONTROLLER':
                if pushmode == 'CUSTOM':
                    payload,code = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='JSON', proxy=proxyDict)
                elif pushmode == 'PUSHGATEWAY':
                    payload,code = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='PUSHGATEWAY', proxy=proxyDict)
            elif nc_mode == 'NGINX_INSTANCE_MANAGER':
                if pushmode == 'CUSTOM':
                    payload,code = nim.nimInstances(fqdn=nc_fqdn, mode='JSON', proxy=proxyDict)
                elif pushmode == 'PUSHGATEWAY':
                    payload,code = nim.nimInstances(fqdn=nc_fqdn, mode='PUSHGATEWAY', proxy=proxyDict)
            elif nc_mode == 'NGINX_MANAGEMENT_SYSTEM':
                if pushmode == 'CUSTOM':
                    payload = nms.nmsInstances(mode='JSON')
                elif pushmode == 'PUSHGATEWAY':
                    payload = nms.nmsInstances(mode='PUSHGATEWAY')
            elif nc_mode == 'BIG_IQ':
                if pushmode == 'CUSTOM':
                    payload,code = bigiq.bigIqInventory(mode='JSON')
                elif pushmode == 'PUSHGATEWAY':
                    payload,code = bigiq.bigIqInventory(mode='PUSHGATEWAY')

            try:
                if username == '' or password == '':
                    if pushmode == 'CUSTOM':
                        # Push json to custom URL
                        r = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, timeout=10,
                                          proxies=proxyDict)
                    elif pushmode == 'PUSHGATEWAY':
                        # Push to pushgateway
                        r = requests.post(pushgatewayUrl, data=payload, timeout=10, proxies=proxyDict)
                else:
                    if pushmode == 'CUSTOM':
                        # Push json to custom URL with basic auth
                        r = requests.post(url, auth=(username, password), data=json.dumps(payload),
                                          headers={'Content-Type': 'application/json'}, timeout=10, proxies=proxyDict)
                    elif pushmode == 'PUSHGATEWAY':
                        # Push to pushgateway
                        r = requests.post(pushgatewayUrl, auth=(username, password), data=payload, timeout=10,
                                          proxies=proxyDict)
            except:
                e = sys.exc_info()[0]
                print(datetime.datetime.now(), counter, 'Pushing stats to', url, 'failed:', e)
            else:
                print(datetime.datetime.now(), counter, 'Pushing stats to', url, 'returncode', r.status_code)

        except:
            print('Exception caught during push')

        counter = counter + 1

        time.sleep(interval)


# Scheduler for automated email reporting
def scheduledEmail(email_server, email_server_port, email_server_type, email_auth_user, email_auth_pass, email_sender,
                   email_recipient, email_interval):
    while True:
        try:
            if nc_mode == 'NGINX_CONTROLLER':
                payload,code = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='JSON', proxy=proxyDict)
                subscriptionId = '[' + payload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'
            elif nc_mode == 'NGINX_INSTANCE_MANAGER':
                payload,code = nim.nimInstances(fqdn=nc_fqdn, mode='JSON', proxy=proxyDict)
                subscriptionId = '[' + payload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'
            elif nc_mode == 'NGINX_MANAGEMENT_SYSTEM':
                payload = nms.nmsInstances(mode='JSON')
                jsonPayload = json.loads(payload)
                subscriptionId = '[' + jsonPayload['subscription']['id'] + '] '
                subjectPostfix = 'NGINX Usage Reporting'
                attachname = 'nginx_report.json'
            elif nc_mode == 'BIG_IQ':
                payload,code = bigiq.bigIqInventory(mode='JSON')
                subscriptionId = ''
                subjectPostfix = 'BIG-IP Usage Reporting'
                attachname = 'bigip_report.json'

            dateNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            message = EmailMessage()
            message['Subject'] = subscriptionId + '[' + dateNow + '] ' + subjectPostfix
            message['From'] = email_sender
            message['To'] = email_recipient
            message.set_content('This is the ' + subjectPostfix + ' for ' + dateNow)

            attachment = json.dumps(payload)
            bs = attachment.encode('utf-8')
            message.add_attachment(bs,maintype='application',subtype='json',filename=attachname)

            if email_server_type == 'ssl':
                context = ssl._create_unverified_context()
                smtpObj = smtplib.SMTP_SSL(email_server, email_server_port, context=context)
            else:
                smtpObj = smtplib.SMTP(email_server, email_server_port)

                if email_server_type == 'starttls':
                    smtpObj.starttls()

            if email_auth_user != '' and email_auth_pass != '':
                smtpObj.login(email_auth_user, email_auth_pass)

            smtpObj.sendmail(email_sender, email_recipient, message.as_string())
            print(datetime.datetime.now(), 'Reporting email successfully sent to', email_recipient)

        except:
            print(datetime.datetime.now(), 'Sending email stats to',email_recipient,'failed:', sys.exc_info())

        time.sleep(email_interval)


# Returns stats in json format
@app.get("/instances")
@app.get("/f5tt/instances")
def getInstances(request: Request):
    if nc_mode == 'NGINX_CONTROLLER':
        reply,code = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='JSON', proxy=proxyDict)
    elif nc_mode == 'NGINX_INSTANCE_MANAGER':
        reply,code = nim.nimInstances(fqdn=nc_fqdn, mode='JSON', proxy=proxyDict)
    elif nc_mode == 'NGINX_MANAGEMENT_SYSTEM':
        reply,code = nms.nmsInstances(mode='JSON')
    elif nc_mode == 'BIG_IQ':
        reply,code = bigiq.bigIqInventory(mode='JSON')

    # gzip responses supported if the client sends header "Accept-Encoding: gzip"
    responseSent = False

    if "Accept-Encoding" in request.headers:
        if request.headers['Accept-Encoding'] == 'gzip':
            deflatedReply = gzip.compress(json.dumps(reply).encode('utf-8'))
            responseSent = True
            return Response(content=deflatedReply,media_type="application/json",headers={ 'Content-Encoding': 'gzip' })

    if responseSent == False:
        return JSONResponse(content=reply,status_code=code)


# Returns stats in prometheus format
@app.get("/metrics")
@app.get("/f5tt/metrics")
def getMetrics():
    if nc_mode == 'NGINX_CONTROLLER':
        reply,code = nc.ncInstances(fqdn=nc_fqdn, username=nc_user, password=nc_pass, mode='PROMETHEUS', proxy=proxyDict)
    elif nc_mode == 'NGINX_INSTANCE_MANAGER':
        reply,code = nim.nimInstances(fqdn=nc_fqdn, mode='PROMETHEUS', proxy=proxyDict)
    elif nc_mode == 'NGINX_MANAGEMENT_SYSTEM':
        reply,code = nms.nmsInstances(mode='PROMETHEUS')
    elif nc_mode == 'BIG_IQ':
        reply,code = bigiq.bigIqInventory(mode='PROMETHEUS')

    return Response(content=reply,media_type="text/plain")


@app.get("/reporting/{reportingType}")
@app.get("/f5tt/reporting/{reportingType}")
def getReporting(reportingType: str):
    if nc_mode == 'BIG_IQ':
        if reportingType == 'xls':
            instancesJson,code = bigiq.bigIqInventory(mode='JSON')

            if code != 200:
                return JSONResponse(content=json.dumps(instancesJson),status_code=code)

            xlsfile=bigiq.xlsReport(instancesJson)
            headers = {
                'Content-Disposition': 'attachment; filename="bigiq-report.xlsx"'
            }

            return StreamingResponse(xlsfile, headers=headers)

    return JSONResponse(content={'error': 'Not found'},status_code=404)


@app.get("/{uri}")
@app.post("/{uri}")
@app.put("/{uri}")
@app.delete("/{uri}")
def not_found(uri: str):
  return JSONResponse(content={'error': 'Not found',},status_code=404)


if __name__ == '__main__':

    if nc_mode != 'NGINX_CONTROLLER' and nc_mode != 'NGINX_INSTANCE_MANAGER' and nc_mode != 'NGINX_MANAGEMENT_SYSTEM' and nc_mode != 'BIG_IQ':
        print('Invalid DATAPLANE_TYPE')
    else:
        # optional HTTP(S) proxy
        if "HTTP_PROXY" in os.environ:
            http_proxy = os.environ['HTTP_PROXY']
            print('Using HTTP Proxy', http_proxy)
        else:
            http_proxy = ''
        if "HTTPS_PROXY" in os.environ:
            https_proxy = os.environ['HTTPS_PROXY']
            print('Using HTTPS Proxy', https_proxy)
        else:
            https_proxy = ''

        proxyDict = {
            "http": http_proxy,
            "https": https_proxy
        }

        # CVE tracking
        nist_apikey = ''
        if "NIST_API_KEY" in os.environ:
            nist_apikey = os.environ['NIST_API_KEY']
            print('CVE Tracking enabled using key', nist_apikey)
        else:
            print(
                'Basic CVE Tracking - for full tracking get a NIST API key at https://nvd.nist.gov/developers/request-an-api-key')

        # Push thread
        if nc_mode == 'BIG_IQ':
            bigiq.init(fqdn=nc_fqdn, username=nc_user, password=nc_pass, nistApiKey=nist_apikey, proxy=proxyDict)
            print('Running BIG-IQ inventory refresh thread')
            inventoryThread = threading.Thread(target=bigiq.scheduledInventory)
            inventoryThread.start()
        elif nc_mode == 'NGINX_MANAGEMENT_SYSTEM':
            nms.init(fqdn=nc_fqdn, username=nc_user, password=nc_pass, nistApiKey=nist_apikey, proxy=proxyDict)

        if "STATS_PUSH_ENABLE" in os.environ:
            if os.environ['STATS_PUSH_ENABLE'] == 'true':
                stats_push_mode = os.environ['STATS_PUSH_MODE']

                if stats_push_mode != 'PUSHGATEWAY' and stats_push_mode != 'CUSTOM':
                    print('Invalid STATS_PUSH_MODE')
                else:
                    stats_push_url = os.environ['STATS_PUSH_URL']
                    if "STATS_PUSH_USERNAME" in os.environ:
                        stats_push_username = os.environ['STATS_PUSH_USERNAME']
                    else:
                        stats_push_username = ''

                    if "STATS_PUSH_PASSWORD" in os.environ:
                        stats_push_password = os.environ['STATS_PUSH_PASSWORD']
                    else:
                        stats_push_password = ''

                    stats_push_interval = int(os.environ['STATS_PUSH_INTERVAL'])

                    print('Pushing stats to', stats_push_url, 'every', stats_push_interval, 'seconds')

                    print('Running push thread')
                    pushThread = threading.Thread(target=scheduledPush, args=(
                    stats_push_url, stats_push_username, stats_push_password, stats_push_interval, stats_push_mode))
                    pushThread.start()

        if "EMAIL_ENABLED" in os.environ:
            if os.environ['EMAIL_ENABLED'] == 'true':
                email_interval = int(os.environ['EMAIL_INTERVAL'])
                email_sender = os.environ['EMAIL_SENDER']
                email_recipient = os.environ['EMAIL_RECIPIENT']
                email_server = os.environ['EMAIL_SERVER']
                email_server_port = os.environ['EMAIL_SERVER_PORT']
                email_server_type = os.environ['EMAIL_SERVER_TYPE']

                if "EMAIL_AUTH_USER" in os.environ and "EMAIL_AUTH_PASS" in os.environ:
                    email_auth_user = os.environ['EMAIL_AUTH_USER']
                    email_auth_pass = os.environ['EMAIL_AUTH_PASS']
                else:
                    email_auth_user = ''
                    email_auth_pass = ''

                print('Email reporting to', email_recipient, 'every', email_interval, 'days')
                print('Running push thread')
                emailThread = threading.Thread(target=scheduledEmail, args=(
                email_server, email_server_port, email_server_type, email_auth_user, email_auth_pass, email_sender,
                email_recipient, email_interval * 60))
                emailThread.start()

        # REST API / prometheus metrics server
        print('Running REST API/Prometheus metrics server')

        f5ttPort = 5000
        f5ttAddress = "0.0.0.0"
        if "F5TT_PORT" in os.environ:
            f5ttPort = os.environ['F5TT_PORT']
        if "F5TT_ADDRESS" in os.environ:
            f5ttAddress = os.environ['F5tt_ADDRESS']

        uvicorn.run("app:app", host=f5ttAddress, port=f5ttPort)
