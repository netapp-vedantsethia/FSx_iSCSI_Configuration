import json
import requests
import time

def lambda_handler(event, context):
    #IGroup creation
    url = "https://{}/api/protocols/san/igroups".format(event['fsxMgmtIp'])
    headers = {
        'authorization': 'Basic {}'.format(event['auth']),
        'content-type': "application/json",
        'accept': "application/json"
    }

    payload = {
      "protocol": "iscsi",
      "initiators.name": [event['iqn']],
      "name": "{}igrp".format(event['prefix']),
      "os_type": event['osType'],
      "svm.name": event['svmName']
    }
    response = requests.post(url, headers=headers, json=payload, verify=False)

    time.sleep(2)

    check1 = requests.get(url, headers=headers, verify=False)
    check1 = str(check1.json())
    if (check1.find("{}igrp".format(event['prefix'])) != -1):
        pass
    else:
        return {
            'statusCode': 400,
            'body': "IGROUP creation failed: "+str(check1)
        }

    for i in range(3):
        #Volume creation
        if(i==0):
            lunSize = event['lunSizeData']
            volSize = 1.1*int(lunSize)
        elif(i==1):
            lunSize = event['lunSizeLog']
            volSize = 1.1*int(lunSize)
        else:
            lunSize = event['lunSizeSnapInfo']
            volSize = 1.1*int(lunSize)
        url = "https://{}/api/storage/volumes".format(event['fsxMgmtIp'])
        payload = {
          "svm.name": event['svmName'],
          "name": "{}vol{}".format(event['prefix'],str(i)),
          "aggregates.name": ["aggr1"],
          "size": str(volSize)+"G",
          "state": "online",
          "tiering.policy": "snapshot-only",
          "space.snapshot.reserve_percent": 0,
          "autosize.mode": "grow",
          "snapshot_policy": "none"
        }
        response = requests.post(url, headers=headers, json=payload, verify=False)

        time.sleep(2)

        check2 = requests.get(url, headers=headers, verify=False)
        check2 = str(check2.json())
        if (check2.find("{}vol{}".format(event['prefix'],str(i))) != -1):
            pass
        else:
            return {
                'statusCode': 400,
                'body': "Volume creation failed: "+str(check2)
            }

        #Lun Creation
        url = "https://{}/api/storage/luns".format(event['fsxMgmtIp'])
        payload = {
          "svm.name": event['svmName'],
          "location.volume.name": "{}vol{}".format(event['prefix'],str(i)),
          "name": "/vol/{}vol{}/{}lun{}".format(event['prefix'],str(i),event['prefix'],str(i)),
          "os_type": event['osLun'],
          "space.size": str(lunSize)+"G"
        }
        response = requests.post(url, headers=headers, json=payload, verify=False)

        time.sleep(2)

        check3 = requests.get(url, headers=headers, verify=False)
        check3 = str(check3.json())
        if (check3.find("/vol/{}vol{}/{}lun{}".format(event['prefix'],str(i),event['prefix'],str(i))) != -1):
            pass
        else:
            return {
                'statusCode': 400,
                'body': "LUN creation failed: "+str(check3)
            }

        #Lun Mapping
        url = "https://{}/api/protocols/san/lun-maps".format(event['fsxMgmtIp'])
        payload = {
          "svm.name": event['svmName'],
          "lun.name": "/vol/{}vol{}/{}lun{}".format(event['prefix'],str(i),event['prefix'],str(i)),
          "igroup.name": "{}igrp".format(event['prefix'])
        }
        response = requests.post(url, headers=headers, json=payload, verify=False)

        time.sleep(2)

        check4 = requests.get(url, headers=headers, verify=False)
        check4 = str(check4.json())
        if (check4.find("/vol/{}vol{}/{}lun{}".format(event['prefix'],str(i),event['prefix'],str(i))) != -1):
            pass
        else:
            return {
                'statusCode': 400,
                'body': "LUN Mapping failed: "+str(check4)
            }
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(response.json())
    }
