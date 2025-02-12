# F5 Telemetry Tracker on BIG-IQ CM Docker

## Description

The `f5tt-bigiq-docker.sh` script can be used to run F5TT as a container on a BIG-IQ CM 8.1 virtual machine.

## Installation

### Optional steps

**Required only if BIG-IQ CM can't connect to the Internet to pull docker images from Docker Hub**

- Download the latest docker image tar.gz file from [releases](https://github.com/fabriziofiorucci/F5-Telemetry-Tracker/releases) to your local host
- Filename is `` F5-Telemetry-Tracker-X.Y.tar.gz ``
- Copy (scp) the tar.gz file to the BIG-IQ CM virtual machine renaming it into ``F5-Telemetry-Tracker.tar.gz`` (replace X.Y with the actual version you downloaded and BIGIQ_IP_ADDRESS with the actual IP address of BIG-IQ CM)

```
$ scp F5-Telemetry-Tracker-X.Y.tar.gz root@BIGIQ_IP_ADDRESS:/shared/images/tmp/F5-Telemetry-Tracker.tar.gz
Password: 
F5-Telemetry-Tracker-1.1.tar.gz                    100%  271MB  82.7MB/s   00:03
$
```

### Mandatory steps

- Copy (scp) `f5tt-bigiq-docker.sh` from to BIG-IQ CM 8.1 instance, under /tmp/

```
$ scp f5tt-bigiq-docker.sh root@bigiq.f5:/tmp/
Password: 
f5tt-bigiq-docker.sh                         100% 2440     4.7MB/s   00:00    
$ 
```

- SSH **as root** to the BIG-IQ CM instance, set the execution attribute and run the script with no parameters to display the help banner

```
$ ssh root@bigiq.f5
Password: 
Last login: Wed Jan 26 16:44:26 2022 from 192.168.1.26
[root@bigiq:Active:Standalone] config # chmod +x /tmp/f5tt-bigiq-docker.sh 
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh 
$ ./f5tt-bigiq-docker.sh 
F5 Telemetry Tracker - https://github.com/fabriziofiorucci/F5-Telemetry-Tracker

 This tool manages F5 Telemetry Tracker running on docker on a BIG-IQ Centralized Manager VM.

 === Usage:

 ./f5tt-bigiq-docker.sh [options]

 === Options:

 -h             - This help
 -l             - Local mode - to be used if BIG-IQ can't connect to the Internet
 -s             - Start F5 Telemetry Tracker
 -k             - Stop (kill) F5 Telemetry Tracker
 -c             - Check F5 Telemetry Tracker run status
 -u [username]  - BIG-IQ username (batch mode)
 -p [password]  - BIG-IQ password (batch mode)
 -f             - Fetch JSON report
 -a [mode]      - All-in-one mode: start F5 Telemetry Tracker, collect JSON report and stop F5 Telemetry Tracker
                        [mode] = "online" if BIG-IQ has Internet connectivity, "offline" otherwise

 === Examples:

 Start:
        Interactive mode (BIG-IQ with Internet connectivity):           ./f5tt-bigiq-docker.sh -s
        Interactive mode (BIG-IQ with no Internet connectivity):        ./f5tt-bigiq-docker.sh -s -l
        Batch mode (BIG-IQ with Internet connectivity):                 ./f5tt-bigiq-docker.sh -s -u [username] -p [password]
        Batch mode (BIG-IQ with no Internet connectivity):              ./f5tt-bigiq-docker.sh -s -l -u [username] -p [password]
 Stop:
        BIG-IQ with Internet connectivity:                              ./f5tt-bigiq-docker.sh -k
        BIG-IQ with no Internet connectivity:                           ./f5tt-bigiq-docker.sh -k -l
 Fetch JSON:
        ./f5tt-bigiq-docker.sh -f
 All-in-one:
        BIG-IQ with Internet connectivity:                              ./f5tt-bigiq-docker.sh -a online
        BIG-IQ with no Internet connectivity:                           ./f5tt-bigiq-docker.sh -a offline
```

## Usage - manual mode

- Start F5 Telemetry Tracker on BIG-IQ CM (BIG-IQ with Internet connectivity). Enter BIG-IQ admin username and the password

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -s
Username: admin
Password: 
-> Starting F5 Telemetry Tracker, please stand by...
-> F5 Telemetry Tracker started on http://192.168.1.71:5000
[root@bigiq:Active:Standalone] config # 
```

- Start F5 Telemetry Tracker on BIG-IQ CM (BIG-IQ with no Internet connectivity). Enter BIG-IQ admin username and the password

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -s -l
-> Running in local mode
Username: admin
Password: 
-> Decompressing F5 Telemetry Tracker docker image
-> Loading F5 Telemetry Tracker docker image
Loaded image: fiorucci/f5-telemetry-tracker:latest
-> Starting F5 Telemetry Tracker, please stand by...
-> F5 Telemetry Tracker started on http://192.168.1.71:5000
[root@bigiq:Active:Standalone] config #
```

- Check F5 Telemetry Tracker status

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -c   
-> F5 Telemetry Tracker running
[root@bigiq:Active:Standalone] config #
```

- Query F5 Telemetry Tracker from another system to get the JSON file. **F5 Telemetry Tracking must be queried from a different system**

Uncompressed output:

```
$ curl http://192.168.1.71:5000/instances
{"instances":[{"bigip":2,"hwTotals":[{"F5-VE":2}],"swTotals":[{"H-VE-AFM":1,"H-VE-AWF":1,"H-VE-LTM":2,"H-VE-APM":1,"H-VE-DNS":1}]}],"details":[{"inventoryTimestamp":1641986071513,"inventoryStatus":"full"[...]}
```

Compressed output:

```
$ curl -s -H "Accept-Encoding: gzip" http://192.168.1.71:5000/instances --output output-json.gz
```

- Stop F5 Telemetry Tracker:

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -k
-> F5 Telemetry Tracker stopped
[root@bigiq:Active:Standalone] config # 
```

## Usage - all-in-one mode

- Start F5 Telemetry Tracker on BIG-IQ CM in All-In-One "online" mode (BIG-IQ with Internet connectivity). Enter BIG-IQ admin username and the password

```
[root@bigiq:Active:Standalone] config # /tmp/f5tt-bigiq-docker.sh -a online
Username: admin
Password: 
-> Starting F5 Telemetry Tracker, please stand by...
-> F5 Telemetry Tracker started on http://192.168.1.71:5000
-> Collecting report...
-> JSON report generated, copy /tmp/20220128-1907-instances.json to your local host using scp
-> F5 Telemetry Tracker stopped
[root@bigiq:Active:Standalone] config #
```

- Start F5 Telemetry Tracker on BIG-IQ CM in All-In-One "offline" mode (BIG-IQ with no Internet connectivity). Enter BIG-IQ admin username and the password

```
[root@bigiq:Active:Standalone] ~ # /tmp/f5tt-bigiq-docker.sh -a offline
-> Running in local mode
Username: admin
Password: 
-> Decompressing F5 Telemetry Tracker docker image
-> Loading F5 Telemetry Tracker docker image
Loaded image: fiorucci/f5-telemetry-tracker:latest
-> Starting F5 Telemetry Tracker, please stand by...
-> F5 Telemetry Tracker started on http://192.168.1.71:5000
-> Collecting report...
-> JSON report generated, copy /tmp/20220128-1910-instances.json to your local host using scp
-> F5 Telemetry Tracker stopped
[root@bigiq:Active:Standalone] config #
```

- Collect (scp) the generated JSON report
