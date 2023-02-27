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
from config import TOKEN, CHAT_ID

r = redis.Redis()


tb = telebot.TeleBot(TOKEN)

while True:
    
    # new url contains these parameters
    """
    Hourly > $25/hr
    No hires
    1 to 9 hires
    10+ hires
    More than 30 hrs/week
    Admin Support
    Data Science & Analvtics
    IT & Networking
    Web, Mobile & Software Dev
    Less than 5 Proposals
    5 to 10 Proposals
    10 to 15 Proposals
    More than 6 months
    Payment verified
    """
    atom_url = f'https://www.upwork.com/nx/jobs/search/?sort=recency&category2_uid=531770282580668416,531770282580668420,531770282580668419,531770282580668418&t=0&client_hires=0,1-9,10-&proposals=0-4,5-9,10-14&workload=full_time&duration_v3=ongoing&payment_verified=1&hourly_rate=25-'
    response = requests.get(atom_url)
    if response.status_code == 200:
        tree = ET.fromstring(response.text)
        for child in tree:
            if child.tag == '{http://www.w3.org/2005/Atom}entry':
                message = f"""Hi! new upwork job posted!\n"""
                is_present = True
                is_fresh = False
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
                            # country
                            country = re.findall('<b>Country</b>:(.*?)<br />', text)
                            if len(country) == 1:
                                message += f"\n𝗖𝗢𝗨𝗡𝗧𝗥𝗬 : {country[0].strip()}"
                            # category
                            category = re.findall('<b>Category</b>:(.*?)<br />', text)
                            if len(category) == 1:
                                message += f"\n𝗖𝗔𝗧𝗘𝗚𝗢𝗥𝗬 : {category[0].strip()}"
                            is_fresh = True
                if not is_present and is_fresh:
                    try:
                        tb.send_message(CHAT_ID, message)
                    except Exception as e:
                        print(f'Error : {str(e)}')
    else:
        tb.send_message(CHAT_ID, f'𝗘𝗥𝗥𝗢𝗥 : {st}\n{response.text}\n{response.status_code} ')
    time.sleep(100)
time.sleep(1200)
