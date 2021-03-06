import os
import json
import time
import datetime
import hashlib
import boto3
from boto3.dynamodb.conditions import Key,Attr
from base64 import b64encode, b64decode
import logging
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    """ Lambda handler for handling INSERT and MODIFY for /msg API gateway endpoint. """
    session = boto3.Session(region_name='us-east-1')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Subscription-6ze2iusjtre3dfalgyxgqfcsxi-dev')
    dynamo_client = session.client('dynamodb')
    ses_client = session.client('ses')
    
    # Initialize Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    resp = {'status': False, 'TotalItems': {}, 'Items': []}

    # global_vars = set_global_vars()

    if not 'Records' in event:
        resp = {'status': False, "error_message": 'No Records found in Event'}
        return resp
    logger.debug(f"Event:{event}")
    for r in event.get('Records'):
        if r.get('eventName') == "MODIFY":
            d = {}
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            d['time'] = time
            d['UID'] = r['dynamodb']['NewImage']['UID']['S']
            d['name'] = r['dynamodb']['NewImage']['name']['S']
            d['cur_price'] = r['dynamodb']['NewImage']['cur_price']['N']
            d['prev_price'] = r['dynamodb']['OldImage']['cur_price']['N']
            d['restock'] = r['dynamodb']['NewImage']['restock_indicator']['N']
            d['url'] = r['dynamodb']['NewImage']['href']['S']
            d['img'] = r['dynamodb']['NewImage']['imagehref']['S']
            msg = table.query(
                IndexName = 'product-email-index',
                KeyConditionExpression=Key('product').eq(d['UID'])
                )
            d['subscription'] = msg['Items']
            if len(d['subscription']) == 0:
                return resp
            if 'Message' in r['dynamodb']['NewImage']:
                d['Message'] = r['dynamodb']['NewImage']['Message']['S']
            resp['Items'].append(d)
            
    if resp.get('Items'):
        resp['status'] = True
        resp['TotalItems'] = {'Received': len(event.get('Records')), 'Processed': len(resp.get('Items'))}
    logger.info(f"resp:{resp}")
    productInfo = resp.get('Items')
    productName = str(productInfo[0]['name'])
    curPrice = float(productInfo[0]['cur_price'])
    prevPrice = productInfo[0]['prev_price']
    isRestock = productInfo[0]['restock']
    scrapeTime = str(productInfo[0]['time'])
    productLink = str(productInfo[0]['url'])
    imageLink = str(productInfo[0]['img'])
    userName = []
    receiver = []
    targetPrice = []
    
    receiverInfo = productInfo[0].get('subscription')
    for emailInfo in receiverInfo:
        userName = emailInfo['username']
        receiver = emailInfo['email']
        targetPrice = float(emailInfo['target'])
    
        # resp['Items']{['UID']['price_change']['restock_indicator']['scrapetime2']}
        subject = '''USCI Subscription state change'''
        
        priceContent = '''Hey ''' + userName + '''!<br>
        
        ''' + productName + ''' in your subscription list got a discount and met your goal at ''' + scrapeTime + '''. <br>
        
        The price was ''' + prevPrice + ''' and now it is only ''' + str(curPrice) + '''. <br>
        
        Click the button to review your subscription and order it quickly! <br>
    
Thanks,
The USCI team
        '''
        
        restockContent = '''Hey ''' + userName + '''!<br> 
        
        ''' + productName + '''in your subscription list got restocked at ''' + scrapeTime + '''.<br> 
        
        Click the button to review your subscription and order it quickly!<br> 
    
Thanks,
The USCI team
        '''
        
        if curPrice <= targetPrice:
            content = priceContent
        
        elif isRestock == 1:
            content = restockContent
        
        else:
            return resp
            
        with open("subscription.html", "r", encoding="utf-8") as file:
            fcontent = file.read()

        sp = BeautifulSoup(fcontent, 'html.parser')

        text0 = sp.prettify()
        
        replaceContent = '<td class="mcnTextContent" style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;" valign="top">\n                    ' + content + '\n'
        
        text1 = text0.replace('<td class="mcnTextContent" style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;" valign="top">\n                    content\n',replaceContent)
        
        text2 = text1.replace('https://mcusercontent.com/b5eaa72530d93a77b6c3bac61/images/fee19beb-96ac-4b5c-9152-c487a483740a.jpeg',imageLink)
        
        text3 = text2.replace('http://link to be replaced',productLink)

        send_email = ses_client.send_email(
            Source="variladim@gmail.com",
            Destination={
                'ToAddresses': [
                    receiver,
                    ]
                },
            Message={
                'Subject': {
                    'Data': subject,
                    },
                'Body': {
                    'Html': {
                        'Data': text3,
                        }
                    }
                }
            )
    logger.info(f"resp:{resp}")
    return resp
