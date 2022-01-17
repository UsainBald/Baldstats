import time
import getpass
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

user = (getpass.getuser())
cfgfile = f"C:/Users/{user}/Appdata/Roaming/Baldstats/settings.cfg"
statsfile = f"C:/Users/{user}/Appdata/Roaming/Baldstats/session_stats.txt"
# APIkey = "f57c9f4a-175b-430c-a261-d8c199abd927"
playerlist = []
totalstats = []
logfile_lastchanged = 0
currentline = 0
cd = 0
session_starttime = ''
stats_before = []
APIkey = ''
baldstatsmode = ''
mode_remembered = False
session_isstarted = False

if not os.path.exists(f"C:/Users/{user}/Appdata/Roaming/Baldstats"):
    os.mkdir(f"C:/Users/{user}/Appdata/Roaming/Baldstats")


def printer(currentplayer):  # nado ubrat' kogda gui budet
    fdc = totalstats[playerlist.index(f'{currentplayer}')][2]
    if fdc == 0:
        fdc = 1
    print(f"{currentplayer}'s kills =", totalstats[playerlist.index(f'{currentplayer}')][1], 'fkdr =',
          (totalstats[playerlist.index(f'{currentplayer}')][1] / fdc, 2))


def overallprint():  # nado ubrat' kogda gui budet
    for curplayer in totalstats:
        session_displayname = curplayer[0]
        _index = playerlist.index(f'{curplayer[0]}')
        session_bwlevel = totalstats[_index][1] - stats_before[_index][1]
        session_xpprogress = totalstats[_index][5] - stats_before[_index][5]
        session_finalk = totalstats[_index][2] - stats_before[_index][2]
        session_finald = totalstats[_index][3] - stats_before[_index][3]
        if session_finald == 0:
            session_finald = 1
        print(' ')
        if baldstatsmode == 'api':
            print(f"{session_displayname}'s level progress =", session_xpprogress)
            print(f"{session_displayname} has gained {session_bwlevel} levels this session")
        print(f"{session_displayname}'s fkdr =", round(session_finalk / session_finald, 2))
        print(f"{session_displayname}'s final kills =", session_finalk)


def checkname(ign):
    url = f"https://api.hypixel.net/player?key={APIkey}&name={ign}"
    req = requests.get(url).json()
    player = req.get('player')
    if player is not None:
        displayname = player.get("displayname")
        uuid = player.get("uuid")
        return [displayname, uuid]
    else:
        if req.get('cause') == "You have already looked up this name recently":
            print('API request error, try again in a moment')
        else:
            print(f'ERROR: no player by the name of {ign} found')
        return ""


def getbwstats(req_player):
    req_displayname = req_player.get('displayname')
    req_uuid = req_player.get('uuid')
    req_achievements = req_player.get('achievements')
    req_bwlevel = req_achievements.get('bedwars_level')
    req_stats = req_player.get('stats')
    req_bedwars = req_stats.get('Bedwars')
    req_xp = req_bedwars.get('Experience')
    req_finalk = req_bedwars.get('final_kills_bedwars')
    if req_finalk is None:
        req_finalk = 0
    req_finald = req_bedwars.get('final_deaths_bedwars')
    if req_finald is None:
        req_finald = 1
    return [req_displayname, req_bwlevel, req_finalk, req_finald, req_uuid, req_xp]


def getstats(name):
    url = f"https://api.hypixel.net/player?key={APIkey}&name={name.strip()}"
    req = requests.get(url).json()
    req_player = req.get('player')
    if req_player is not None:
        a = getbwstats(req_player)
        print(a)
        return a
    else:
        try:
            ind = playerlist.index(name)
            uuid_req = totalstats[ind][4]
            url = f"https://api.hypixel.net/player?key={APIkey}&uuid={uuid_req}"
            req = requests.get(url).json()
            req_player = req.get('player')
            if req_player is not None:
                a = getbwstats(req_player)
                return a
        except ValueError:
            pass


def urllist(nicklist):
    urls = []
    for i in nicklist:
        url = f"https://api.hypixel.net/player?key={APIkey}&name={i}"
        urls.append(url)
    return urls


def mtrequest(names):
    with ThreadPoolExecutor(80) as executor:
        for name in names:
            executor.submit(addplayer, name)


def addplayer(newplayer):
    newplayer = newplayer.strip()
    if newplayer not in playerlist:
        a = getstats(newplayer)
        playerlist.append(newplayer)
        totalstats.append(a)
        if session_isstarted:
            stats_before.append(a)
        print(f'{newplayer} was added')
        print(totalstats)
        print(playerlist)


def removeplayer(kickedplayer):
    kickedplayer = kickedplayer.strip()
    if kickedplayer in playerlist:
        del totalstats[playerlist.index(kickedplayer)]
        del playerlist[playerlist.index(kickedplayer)]
        print(f"{kickedplayer} was removed")
    else:
        print(f'ERROR: {kickedplayer} is not in the list')
        

def disband_party():
    global totalstats
    global playerlist
    totalstats = [totalstats[0]]
    playerlist = [playerlist[0]]
    

def checkclient():
    client = 0
    edit_lastchanged = 0
    for i in clientlist:
        if os.path.exists(i):
            if os.stat(i).st_mtime > edit_lastchanged:
                edit_lastchanged = os.stat(i).st_mtime
                client = i
    if client != 0:
        return client
    else:
        print("You don't have minecraft installed")


def choosemode():
    global baldstatsmode
    global mode_remembered
    baldstatsmode = False
    mode_remembered = False
    if os.path.exists(cfgfile):
        with open(cfgfile) as cfg:
            for cfgline in cfg:
                s = cfgline.split('=')
                if s[0] == 'RememberMode':
                    mode_remembered = True
                    if s[1].strip() == 'logfile':
                        baldstatsmode = 'logfile'
                    elif s[1].strip() == 'api':
                        baldstatsmode = 'api'
    if not baldstatsmode:
        print('CHOOSE BALDSTATS MODE')
        print('Type 1 to get stats from the log file (updates in real time, unable to track stats of nicked players)')
        print('Type 2 to get stats from the API (updates once every 30 seconds, tracks stats of nicked players)')
        m = int(input())
        if m == 1:
            baldstatsmode = 'logfile'
        elif m == 2:
            baldstatsmode = 'api'
        else:
            raise SystemError


def remembermode():
    global baldstatsmode
    global mode_remembered
    if not mode_remembered:
        print('Do you want to remember your choice?')
        print('y - yes')
        print('n - no')
        m = input()
        if m == 'y':
            with open(cfgfile, 'a+') as cfg:
                cfg.write(f'RememberMode={baldstatsmode}' + '\n')


def get_api_key():
    global APIkey
    apikey = False
    apikeycheck = False
    if os.path.exists(cfgfile):
        with open(cfgfile) as cfg:
            for cfgline in cfg:
                s = cfgline.split('=')
                if s[0] == 'API_KEY':
                    APIkey = s[1].strip()
                    while not apikey:
                        req_link = f'https://api.hypixel.net/player?key={APIkey}'
                        if requests.get(req_link) == '<Response [403]>':
                            print('Invalid API key, try again')
                            APIkey = input()
                        else:
                            cfg.write(f'API_KEY={APIkey}' + '\n')
                            apikey = True
    if not apikey:
        print('Enter your hypixel API key (you can get it by using /api new on the server)')
        while not apikeycheck:
            APIkey = input()
            req_link = f'https://api.hypixel.net/player?key={APIkey}'
            if requests.get(req_link) == '<Response [403]>':
                print('Invalid API key, try again')
            else:
                with open(cfgfile, 'a+') as cfg:
                    cfg.write(f'API_KEY={APIkey}' + '\n')
                apikeycheck = True


def startsession():
    global session_starttime
    global stats_before
    global session_isstarted
    global totalstats
    session_starttime = str(datetime.now())[:16]
    stats_before = [i[:] for i in totalstats]
    session_isstarted = True


def endsession():
    global session_isstarted
    session_isstarted = False
    pass


get_api_key()

if os.path.exists(cfgfile):
    with open(cfgfile) as cfg:
        ignentered = False
        for cfgline in cfg:
            s = cfgline.split('=')
            if s[0] == 'Name':
                ign = s[1]
                ignentered = True
while not ignentered:
    ign = input('Enter your minecraft nickname' + '\n')
    ign = checkname(ign)[0]
    uuid = checkname(ign)[1]
    if ign != "":
        with open(cfgfile, 'a+') as cfg:
            cfg.write(f'Name={ign}={uuid}' + '\n')
            ignentered = True

with open(cfgfile) as cfg:
    for cfgline in cfg:
        s = cfgline.split('=')
        if s[0] == 'Name':
            playerlist.append('dababy2012_YT')
            totalstats = [['dababy2012_YT', 40, 1400, 200, 'dsadas', 321312]]
            # addplayer(s[1])

lunar_client = f"C:/Users/{user}/.lunarclient/offline/1.8/logs/latest.log"
minecraft_client = f"C:/Users/{user}/AppData/Roaming/.minecraft/logs/latest.log"
badlion_client = f"C:/Users/{user}/AppData/Roaming/.minecraft/logs/blclient/chat/latest.log"
pvplounge_client = f"C:/Users/{user}/AppData/.pvplounge/logs/latest.log"
clientlist = [lunar_client, minecraft_client, badlion_client, pvplounge_client]

logfile = checkclient()

if logfile == badlion_client:
    print('Linked to Badlion Client')
elif logfile == minecraft_client:
    print('Linked to the Official Launcher')
elif logfile == lunar_client:
    print('Linked to Lunar Client')
elif logfile == pvplounge_client:
    print('Linked to PVPLounge Client')

choosemode()
remembermode()
startsession()

for i in playerlist:
    print('Current party:')
    print(i)

with open(logfile) as f:
    currentline = len(f.readlines())  # finding the last line

while True:
    if os.stat(logfile).st_mtime > logfile_lastchanged:
        with open(logfile) as f:
            length = len(f.readlines())
        for line in range(currentline, length):
            with open(logfile) as f:
                lastline = f.readlines()[line].strip()
            logfile_lastchanged = os.stat(logfile).st_mtime
            currentline = line + 1
            if lastline[11:31] == '[Client thread/INFO]':
                s = lastline.split()[4:]
                for i in range(len(s)):
                    if s[i][0] == '[' and s[i][-1] == ']':
                        del s[i]
                        break
                len_s = len(s)
                if len_s == 4:
                    # player joins the party (works)
                    if s[1] == 'joined' and s[3] == 'party.':
                        addplayer(s[0])
                    # you leave the party (works)
                    if s[0] == 'You' and s[1] == 'left':
                        disband_party()
                        print('You left the party')

                if len_s == 5:
                    # player leaves the party (works)
                    if s[2] == 'left' and s[4] == 'party.':
                        removeplayer(s[0])
                    # you joined someone else's party (works)
                    elif s[0] == 'You' and s[4] == 'party!':
                        addplayer(s[3][:-2])
                    # someone disbands the party (should work)
                    elif s[1] == 'has' and s[2] == 'disbanded':
                        disband_party()

                if len_s == 7:
                    # player gets removed from the party (should work)
                    if s[1] == 'has' and s[3] == 'removed':
                        removeplayer(s[0])

                if len_s == 9:
                    # player gets removed from the party (should work)
                    if s[1] == 'was' and s[2] == 'removed':
                        removeplayer(s[0])

                if len_s == 14:
                    # the party gets disbanded (idk if it works)
                    if s[1] == 'party' and s[3] == 'disbanded':
                        disband_party()
                if len_s > 0:
                    if s[0] == "You'll":
                        # You join a party with multiple players in it (works)
                        s2 = lastline.split(':')
                        namelist = []
                        s = s2[3].split()
                        if len_s >= 4:
                            if s[1] == "You'll":
                                pl = s2[4].split(',')
                                for m in pl:
                                    n = m.split()
                                    ap = n[-1]
                                    namelist.append(ap)
                                mtrequest(namelist)
                if baldstatsmode == 'logfile':
                    if lastline[-11:] == 'FINAL KILL!':
                        for player in playerlist:
                            playerstr = f'{player}'.strip()
                            if playerstr in lastline:
                                a = playerlist.index(playerstr)
                                if not playerstr == s[4]:
                                    totalstats[a][2] += 1
                                else:
                                    totalstats[a][3] += 1
                                overallprint()
                elif baldstatsmode == 'api':
                    if cd <= time.time() - 30:
                        cd = time.time()
                        for i in playerlist:
                            getstats(i)
                            overallprint()

    else:
        time.sleep(0.01)
