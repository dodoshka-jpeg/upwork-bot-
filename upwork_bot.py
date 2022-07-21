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
search_terms = ['long term python',
                'full time python',
                'long term software engineer',
                'full time software',
                'scraping',
                'automation',
                'scripting',
                'back end',
                'software engineer']

tb.polling()
# tb.send_message(CHAT_ID, "*bold \*text*")
# Use none_stop flag let polling will not stop when get new message occur error.
tb.polling(none_stop=True)
# Interval setup. Sleep 3 secs between request new message.
tb.polling(interval=3)

while True:
    for st in search_terms:
        url_string = urllib.parse.quote_plus(st)
        atom_url = f'https://www.upwork.com/ab/feed/jobs/atom?q={url_string}&sort=client_rating+desc&category2_uid=531770282580668420%2C531770282580668418&duration_v3=ongoing&verified_payment_only=1&location=Americas&paging=0%3B50&api_params=1&securityToken=86f7f2309fbbaf6c2851ac3fbc60f9fa1f9d2c1da216a37b4284547b3db87e3d0ad6fd5f170972dbdb01269e109971a68c2a761d4dbe2221a165f8f6f6449751&userUid=1250753516040204288&orgUid=1250753516048592897&ptc=1379092697657143296'
        response = requests.get(atom_url)
        if response.status_code == 200:
            tree = ET.fromstring(response.text)
            for child in tree:
                if child.tag == '{http://www.w3.org/2005/Atom}entry':
                    is_fresh = True
                    message = f"""Hi! new upwork job posted!\n"""
                    for entry_child in child:
                        if entry_child.tag == '{http://www.w3.org/2005/Atom}id':
                            job_url = entry_child.text.replace('?source=rss', '')
                            hash = hashlib.sha224(job_url.encode()).hexdigest()
                            if not r.get(hash):
                                r.mset({hash: job_url})
                            else:
                                continue
                            message += f"\n𝗟𝗜𝗡𝗞 : {job_url}"
                        elif entry_child.tag == '{http://www.w3.org/2005/Atom}title':
                            title = entry_child.text
                            message += f"\n𝗧𝗜𝗧𝗟𝗘 : {title}"
                        elif entry_child.tag == '{http://www.w3.org/2005/Atom}summary':
                            text = entry_child.text.replace('\r', '').replace('\n', '')
                            date = parser.parse(re.findall('<b>Posted On</b>:(.*?)<br />', text)[0].strip())
                            final_date = date.astimezone(tz=gettz('Asia/Kolkata'))
                            message += f"\n𝗣𝗢𝗦𝗧𝗘𝗗 𝗢𝗡 : {str(final_date)}"
                            current_date = datetime.now(tz=gettz('Asia/Kolkata'))
                            if (current_date - final_date).days < 3:
                                # hourly range:
                                hourly_range = re.findall('<b>Hourly Range</b>:(.*?)<br />', text)
                                if len(hourly_range) == 1:
                                    message += f"\n𝗛𝗢𝗨𝗥𝗟𝗬 : {hourly_range[0].strip()}"
                                # budget
                                budget = re.findall('𝗕𝗨𝗗𝗚𝗘𝗧:(.*?)<br />', text)
                                if len(budget) == 1:
                                    message += f"\n *BUDGET* : {budget[0].strip()}"

                                # category
                                category = re.findall('<b>Category</b>:(.*?)<br />', text)
                                if len(category) == 1:
                                    message += f"\n𝗖𝗔𝗧𝗘𝗚𝗢𝗥𝗬 : {category[0].strip()}"

                                tb.send_message(CHAT_ID, message)
        else:
            tb.send_message(CHAT_ID, f'𝗘𝗥𝗥𝗢𝗥 : {st}\n{response.text}\n{response.status_code} ')
        time.sleep(100)
    time.sleep(1200)
