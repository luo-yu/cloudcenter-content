#!/usr/bin/python
# -*- coding: utf-8 -*-

# Deployment cleanup script

import requests, pdb, sys, json
from requests.auth import HTTPBasicAuth
import argparse
import pdb

requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument("username", help="Your API username. Not the same as your UI Login. See your CloudCenter admin for help.")
parser.add_argument("apiKey", help="Your API key.")
parser.add_argument("ccm", help="CCM hostname or IP.")
parser.add_argument("-o", "--overwrite", action='store_true', help="When importing, overwrite existing service in CloudCenter. When exporting, overwrite existing file.")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-e", "--export", dest="e", metavar='servicename', help="(text, not int) Service ID of the service that you want to export.")
group.add_argument("-i", "--import", dest="i", metavar='filename', help="Filename of the service that you want to import.", type=argparse.FileType('r'))

args = parser.parse_args()
parser.parse_args()

username = args.username
apiKey = args.apiKey
ccm = args.ccm
baseUrl = "https://"+args.ccm

s = requests.Session()


def getTenantId():
    url = baseUrl+"/v1/users"

    querystring = {}

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    response = s.request("GET", url, headers=headers, params=querystring, verify=False, auth=HTTPBasicAuth(username, apiKey))

    j = response.json()
    tenantId = None
    for user in j['users']:
        #print(json.dumps(user['username'], indent=2))
        if user['username'] == username:
            tenantId = user['tenantId']
            break
    if not tenantId:
        print("Couldn't find tenantId")
        sys.exit(1)
    return tenantId

def getServiceId(tenantId, serviceName):
    url = baseUrl+"/v1/tenants/"+tenantId+"/services/"

    querystring = {
        "size" : 0
    }

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    response = s.request("GET", url, headers=headers, params=querystring, verify=False, auth=HTTPBasicAuth(username, apiKey))

    j = response.json()
    serviceId = None
    for service in j['services']:
        #print(json.dumps(user['username'], indent=2))
        if service['name'] == serviceName:
            serviceId = service['id']

    return serviceId

def getImageId(tenantId, imageName):
    url = baseUrl+"/v1/tenants/"+tenantId+"/images/"

    querystring = {
        "size" : 0
    }

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    response = s.request("GET", url, headers=headers, params=querystring, verify=False, auth=HTTPBasicAuth(username, apiKey))

    j = response.json()
    imageId = None
    for image in j['images']:
        #print(json.dumps(user['username'], indent=2))
        if image['name'] == imageName:
            imageId = image['id']

    return imageId

def getImageName(tenantId, imageId):
    url = baseUrl+"/v1/tenants/"+tenantId+"/images/"

    querystring = {
        "size" : 0
    }

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    response = s.request("GET", url, headers=headers, params=querystring, verify=False, auth=HTTPBasicAuth(username, apiKey))

    j = response.json()
    imageName = None
    for image in j['images']:
        #print(json.dumps(user['username'], indent=2))
        if int(image['id']) == imageId:
            imageName = image['name']

    return imageName

def getServiceManifest(serviceName):
    tenantId = getTenantId()
    serviceId = getServiceId(tenantId, serviceName)

    if not serviceId:
        print("Couldn't find serviceId for service {} in tenant Id {}".format(serviceName, tenantId))
        sys.exit(1)

    url = baseUrl+"/v1/tenants/"+tenantId+"/services/"+serviceId

    querystring = {}

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    response = s.request("GET", url, headers=headers, params=querystring, verify=False, auth=HTTPBasicAuth(username, apiKey))

    j = response.json()

    # Add a custom attribute to persist the name of the default image which makes this portal. The
    # default image Id won't be. Remove the default image Id for safety.
    j['defaultImageName'] = getImageName(tenantId, j['defaultImageId'])
    j.pop("defaultImageId", None)

    # Get rid of these instance/user/tenant-specific parameters to make it importable.
    j.pop("id", None)
    j.pop("logoPath", None)
    j.pop("ownerUserId", None)
    j.pop("resource", None)


    return j

# Get the name of the service from the JSON
def getServiceName(serviceJson):
    serviceName = serviceJson['name']
    return(serviceName)

# Return a list of images used in the service
def getImagesFromService(serviceJson):
    images = []
    for image in serviceJson['images']:
        images.append(image['name'])

    return images

def getImages():
    tenantId = getTenantId()
    url = baseUrl+"/v1/tenants/"+tenantId+"/images"

    querystring = {}

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    response = s.request("GET", url, headers=headers, params=querystring, verify=False, auth=HTTPBasicAuth(username, apiKey))

    j = response.json()

    images = []
    for image in j['images']:
        images.append(image['name'])
    return images

def createImage(image):
    tenantId = getTenantId()
    url = baseUrl+"/v1/tenants/"+tenantId+"/images"

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    image.pop('id', None)
    image.pop('resource', None)
    image.pop('systemImage', None)

    response = s.request("POST", url, headers=headers, data=json.dumps(image), verify=False, auth=HTTPBasicAuth(username, apiKey))
    newImage = response.json()
    print(json.dumps(newImage, indent=2))
    print("Image {} created with ID {}".format(newImage['name'], int(newImage['id'])))
    return int(response.json()['id'])


# Import the service into a CloudCenter instance
def importService(serviceJson):
    tenantId = getTenantId()
    serviceName = getServiceName(serviceJson = serviceJson)
    serviceId = getServiceId(tenantId = tenantId, serviceName = serviceName)
    serviceJson.pop("id", None)
    serviceJson.pop("logoPath", None)
    serviceJson.pop("ownerUserId", None)
    serviceJson.pop("resource", None)

    # Update all the imageIds in the service to match the ones in the instance that you're importing into.
    for image in serviceJson['images']:
        imageId = getImageId(tenantId, image['name'])
        if imageId:
            image['id'] = imageId
            # This just sets the default image Id to whichever of the images comes through this loop LAST.
            serviceJson['defaultImageId'] = imageId
        else:
            print("Image {} not found. I will create it so that the service will import, but it will be UNMAPPED."
                  "You will have to create the worker if necessary and map it yourself.".format(image['name']))
            image['id'] = createImage(image)

    # Assume that key defaultImageName was properly inserted into the exported JSON, then use that to get correct
    # Image Id for the defalt Image.
    serviceJson['defaultImageId'] = getImageId(tenantId, serviceJson['defaultImageName'])

    headers = {
        'x-cliqr-api-key-auth': "true",
        'accept': "application/json",
        'content-type': "application/json",
        'cache-control': "no-cache"
    }
    if serviceId:
        print("Service ID: {} for service {} found in the CloudCenter instance.".format(serviceId, serviceName))
        if not args.overwrite:
            print("--overwrite not specified. Exiting")
            sys.exit()
        else:
            print("--overwrite specified. Updating existing service.")
            url = baseUrl+"/v1/tenants/"+tenantId+"/services/"+serviceId
            serviceJson['id'] = serviceId
            response = s.request("PUT", url, headers=headers, data=json.dumps(serviceJson), verify=False, auth=HTTPBasicAuth(username, apiKey))
            print(json.dumps(response.json(), indent=2))
    else:
        print("Service ID for service {} not found. Creating".format(serviceName))
        url = baseUrl+"/v1/tenants/"+tenantId+"/services/"
        response = s.request("POST", url, headers=headers, data=json.dumps(serviceJson), verify=False, auth=HTTPBasicAuth(username, apiKey))
        print(json.dumps(response.json(), indent=2))
        print("Service {} created with Id {}".format(serviceName, response.json()['id']))





# TODO: Check for existing file and properly use the overwrite flag.
if args.e :
    serviceName = args.e
    print("Exporting service: {}".format(serviceName))
    j = getServiceManifest(serviceName)
    filename = "{serviceName}.servicemanifest".format(serviceName=serviceName)
    with open(filename, 'w') as f:
        json.dump(j, f, indent=4)

    print("Service {} exported to {}".format(serviceName, filename))

if args.i :
    serviceJson = json.load(args.i)

    importService(serviceJson)




