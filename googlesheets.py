# -*- coding: utf-8 -*-
from __future__ import print_function
import httplib2
import os
import time
import json
import shopify
import configparser
import requests

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Hunger Work Studio Orders'

# SHOPIFY Portion
config = configparser.ConfigParser()
config.read('shopify.ini')

API_KEY = config['SHOPIFY']['API_KEY']
PASSWORD = config['SHOPIFY']['PASSWORD']
SHOP_NAME = config['SHOPIFY']['SHOP_NAME']

shop_url = "https://%s:%s@%s.myshopify.com/admin" % (API_KEY, PASSWORD, SHOP_NAME)
shopify.ShopifyResource.set_site(shop_url)
shop = shopify.Shop.current()

# Grab Shopify Orders
order_url = "https://%s:%s@%s.myshopify.com/admin/orders.json" % (API_KEY, PASSWORD, SHOP_NAME)
response = requests.get(order_url)
json_data = json.loads(response.content)

# write to file (optional; uncomment to enable)
# filename = 'orders-[%s].txt' % time.ctime()

# with open('neworders1.txt', 'w') as outfile:
    # json.dump(json_data, outfile)

# Save Order details into python dictionary to send to Google Sheets API
ordersData = []
orderDetails = ['Last Updated', 'Email', 'IP', 'Title', 'Properties']
# orderDetails = ['Email', 'IP', 'Title', 'Name1', 'Value1', 'Name2', 'Value2', 'Name3', 'Value3', 'Name4', 'Value4', 'Name5', 'Value5']
ordersData += [orderDetails]

for i in json_data['orders']:
    for line in i['line_items']:
        # Check for specific order name
        if 'Create/Update Event Entry' in line['title']:
            lastUpdated = i['updated_at']
            title = line['title']
            # for item in line['properties']:
                # for key, val in item.items():
                    # vals = "{0}:{1}".format(key, val)
                    # ordersData.append([vals])
                    # print("{0}:{1}".format(key, val))
                    # ordersData[3:] = key
                    # ordersData[4:] = val
                # properties = str(item)
            properties = str(line['properties'])
            ip = i['client_details']['browser_ip']
            try:
                email = i['customer']['email']
            except KeyError:
                # no email
                print('No email for order')
                email = 'No email for order'

            ordersData.append([lastUpdated, email, ip, title, properties])

            # for item in line['properties']:
                # print(item)
                # for key, val in item.items():
                    # ordersData.append(key)


dataToInsert = { 'values': ordersData }


# Google Sheets API authentication
def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """ Authenticate with OAuth, create a timestamped Sheet with orders
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    # data = {'properties': {'title': 'Hunger Work Studio Orders [%s]' % time.ctime()}}
    # res = service.spreadsheets().create(body=data).execute()
    # SHEET_ID = res['spreadsheetId']
    # print('Created "%s"' % res['properties']['title'])
    # print(SHEET_ID)
    
    data = dataToInsert
    
    SHEET_ID = '1dO3YavokqF72F_tzXhiw-OJdXy5MkBhDxtT3rSmfBzo'

    service.spreadsheets().values().update(spreadsheetId=SHEET_ID,
        range='Sheet1', body=data, valueInputOption='RAW').execute()
    print('Wrote data to Sheet:')
    rows = service.spreadsheets().values().get(spreadsheetId=SHEET_ID,
        range='Sheet1').execute().get('values', [])
    for row in rows:
        print(row)

if __name__ == '__main__':
    main()
