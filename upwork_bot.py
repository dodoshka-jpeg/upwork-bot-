import time

import telebot
import xml.etree.ElementTree as ET
import urllib
import requests
import hashlib
import re
from dateutil import parser
from datetime import datetime
from dateutil.tz import gettz
import redis


r = redis.Redis()
TOKEN = "5465920435:AAGhPtezNseQr0wiIPwtoMT6HQRtY2GEWO8"
CHAT_ID = '772146169'

tb = telebot.TeleBot(TOKEN)
search_terms = ['python developer',
                'scraping',
                'scripting',
                'software engineer',
                'backend developer',
                'full time developer']

while True:
    for st in search_terms:
        url_string = urllib.parse.quote_plus(st)
        atom_url = f'https://www.upwork.com/ab/feed/jobs/atom?q={url_string}&sort=recency&client_hires=1-9%2C10-&proposals=0-4%2C5-9%2C10-14&workload=full_time&duration_v3=ongoing&verified_payment_only=1&paging=0%3B50&api_params=1&securityToken=86f7f2309fbbaf6c2851ac3fbc60f9fa1f9d2c1da216a37b4284547b3db87e3d0ad6fd5f170972dbdb01269e109971a68c2a761d4dbe2221a165f8f6f6449751&userUid=1250753516040204288&orgUid=1250753516048592897&ptc=1379092697657143296'
        response = requests.get(atom_url)
        if response.status_code == 200:
            tree = ET.fromstring(response.text)
            for child in tree:
                if child.tag == '{http://www.w3.org/2005/Atom}entry':
                    message = f"""Hi! new upwork job posted!\n"""
                    is_present = True
                    for entry_child in child:
                        if entry_child.tag == '{http://www.w3.org/2005/Atom}id':
                            job_url = entry_child.text.replace('?source=rss', '')
                            hashed_url = hashlib.sha224(job_url.encode()).hexdigest()
                            if not r.get(hashed_url):
                                r.mset({hashed_url: job_url})
                                is_present = False
                            message += f"\n𝗟𝗜𝗡𝗞 : {job_url}"
                        elif entry_child.tag == '{http://www.w3.org/2005/Atom}title':
                            title = entry_child.text
                            message += f"\n𝗧𝗜𝗧𝗟𝗘 : {title}"
                        elif entry_child.tag == '{http://www.w3.org/2005/Atom}summary':
                            text = entry_child.text.replace('\r', '').replace('\n', '')
                            date = parser.parse(re.findall('<b>Posted On</b>:(.*?)<br />', text)[0].strip())
                            final_date = date.astimezone(tz=gettz('Asia/Kolkata'))
                            current_date = datetime.now(tz=gettz('Asia/Kolkata'))
                            days = (current_date - final_date).days
                            if days < 3:
                                # hourly range:
                                message += f"\n𝗗𝗔𝗬 : {str(days)}"
                                hourly_range = re.findall('<b>Hourly Range</b>:(.*?)<br />', text)
                                if len(hourly_range) == 1:
                                    message += f"\n𝗛𝗢𝗨𝗥𝗟𝗬 : {hourly_range[0].strip()}"
                                # budget
                                budget = re.findall('<b>Budget</b>:(.*?)<br />', text)
                                if len(budget) == 1:
                                    message += f"\n𝗕𝗨𝗗𝗚𝗘𝗧 : {budget[0].strip()}"

                                # category
                                category = re.findall('<b>Category</b>:(.*?)<br />', text)
                                if len(category) == 1:
                                    message += f"\n𝗖𝗔𝗧𝗘𝗚𝗢𝗥𝗬 : {category[0].strip()}"
                    if not is_present:
                        tb.send_message(CHAT_ID, message)
        else:
            tb.send_message(CHAT_ID, f'𝗘𝗥𝗥𝗢𝗥 : {st}\n{response.text}\n{response.status_code} ')
        time.sleep(100)
    time.sleep(1200)
