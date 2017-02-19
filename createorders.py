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
    """ Authenticate with OAuth
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    
    # TEST Winners Spreadhsheet
    SHEET_ID = '11sCwiyjN8reAMQDW6GJdvwed493Ubv0Lv1F5EV-4Xwk'

    rows = service.spreadsheets().values().get(spreadsheetId=SHEET_ID,
        range='A2:Z1000').execute().get('values', [])
        
    for row in rows:
        email_list = row[0].split(',')
        id_list = row[1].split(',')
        item_list = row[2].split(',')
        price_list = row[3].split(',')
        quantity_list = row[4].split(',')

        line_items = [{ "title": item, "price": int(price), "quantity": quantity } for item, price, quantity in zip(item_list, price_list, quantity_list)]

        order = {"email": email_list[0], "send_receipt": True, "customer": { "id": id_list[0] },  "use_customer_default_address": True, "line_items": line_items }
    
        # Create Draft Orders
        order_url = "https://%s:%s@%s.myshopify.com/admin/draft_orders.json" % (API_KEY, PASSWORD, SHOP_NAME)
        payload = {"draft_order": order}
        headers = {'content-type': 'application/json'}
        response = requests.post(order_url, data=json.dumps(payload), headers=headers)
        json_data = json.loads(response.content)

        # Send invoices
        order_id = json_data['draft_order']['id']
        invoice_url = "https://%s:%s@%s.myshopify.com/admin/draft_orders/%s/send_invoice.json" % (API_KEY, PASSWORD, SHOP_NAME, order_id)
        invoice_data = { "subject": "HWS INVOICE YEAAAAHHHH BOI!", "custom_message": "Boom." }
        invoice_payload = {"draft_order_invoice": invoice_data}
        invoice_headers = {'content-type': 'application/json'}
        invoice_response = requests.post(invoice_url, data=json.dumps(invoice_payload), headers=invoice_headers)
        invoice_response_json = json.loads(invoice_response.content)

        print(invoice_response_json)
if __name__ == '__main__':
    main()
