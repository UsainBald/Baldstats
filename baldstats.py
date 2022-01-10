import time
import getpass
import os
import requests
from concurrent.futures import ThreadPoolExecutor

user = (getpass.getuser())
cfgfile = r"C:\Users" + f"\{user}\Appdata\Roaming\Baldstats\cfg.txt"
API_KEY = "f57c9f4a-175b-430c-a261-d8c199abd927"
playerlist = []
totalstats = []
nicks = []
nickedplayers = []
nickedlist = []
logfile_lastchanged = 0
currentline = 0


def printer(currentplayer):
    fdc = totalstats[playerlist.index(f'{currentplayer}')][2]
    if fdc == 0:
        fdc = 1
    print(f"{currentplayer}'s kills =", totalstats[playerlist.index(f'{currentplayer}')][1], 'fkdr =',
          (totalstats[playerlist.index(f'{currentplayer}')][1] / fdc, 2))


def checkname(ign):
    url = f"https://api.hypixel.net/player?key={API_KEY}&name={ign}"
    req = requests.get(url).json()
    player = req.get('player')
    if player is not None:
        displayname = player.get("displayname")
        return displayname
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
    req_finalk = req_bedwars.get('final_kills_bedwars')
    if req_finalk is None:
        req_finalk = 0
    req_finald = req_bedwars.get('final_deaths_bedwars')
    if req_finald is None:
        req_finald = 1
    return [req_displayname, req_bwlevel, req_finalk, req_finald, req_uuid]


def getstats(name):
    url = f"https://api.hypixel.net/player?key={API_KEY}&name={name}"
    req = requests.get(url).json()
    req_player = req.get('player')
    if req_player is not None:
        a = getbwstats(req_player)
        return a
    else:
        try:
            ind = playerlist.index(name)
        except ValueError:
            pass
        uuid_req = totalstats[ind][4]
        url = f"https://api.hypixel.net/player?key={API_KEY}&uuid={name}"
        req = requests.get(url).json()
        req_player = req.get('player')
        if req_player is not None:
            a = getbwstats(req_player)
            return a


def urllist(nicklist):
    urls = []
    for i in nicklist:
        url = f"https://api.hypixel.net/player?key={API_KEY}&name={i}"
        urls.append(url)
    return urls


def mtrequest(names):
    with ThreadPoolExecutor(80) as executor:
        for name in names:
            executor.submit(addplayer, name)


def addplayer(newplayer):
    if newplayer not in playerlist:
        a = getstats(newplayer)
        playerlist.append(newplayer)
        totalstats.append(a)
        print(f'{newplayer} was added')


def removeplayer(kickedplayer):
    if kickedplayer in playerlist:
        del totalstats[playerlist.index(kickedplayer)]
        del playerlist[playerlist.index(kickedplayer)]
        print(f"{kickedplayer} was removed")
    else:
        print('ERROR: this player is not in the list')


def overallprint():
    print(' ')
    print('OVERALL STATS:')
    for i in totalstats:
        fdc = totalstats[playerlist.index(f'{i[0]}')][2]
        if fdc == 0:
            fdc = 1
        print(' ')
        print(f"{i[0]}'s fkdr =", round(
            totalstats[playerlist.index(f'{i[0]}')][1] / fdc, 2))
        print(f"{i[0]}'s final kills =",
              totalstats[playerlist.index(f'{i[0]}')][1])
        print(f"{i[0]}'s final deaths =",
              totalstats[playerlist.index(f'{i[0]}')][2])


def checkclient():
    edit_lastchanged = 0
    for i in clientlist:
        if os.path.exists(i):
            if os.stat(i).st_mtime > edit_lastchanged:
                edit_lastchanged = os.stat(i).st_mtime
                client = i
    try:
        return client
    except Exception:
        print("You don't have minecraft installed")


ignnotentered = True
if not os.path.exists(cfgfile):
    while ignnotentered:
        ign = input('Enter your minecraft ign\n')
        ign = checkname(ign)
        if ign != "":
            os.mkdir(f"C:\Users\{user}\Appdata\Roaming\Baldstats")
            with open(cfgfile, 'w') as cfg:
                cfg.write(f'Name = {ign}')
                ignnotentered = False

with open(cfgfile) as cfg:
    for cfgline in cfg:
        s = cfgline.split()
        addplayer(s[2])
        cfgplayer = s[2]

a = '1.8'
blclient = 'blclient'
lunar_client = f"C:\Users\{user}\.lunarclient\offline\{a}\logs\latest.log"
minecraft_client = f"C:\Users\{user}\AppData\Roaming\.minecraft\logs\latest.log"
badlion_client = f"C:\Users\{user}\AppData\Roaming\.minecraft\logs\{blclient}\chat\latest.log"
pvplounge_client = f"C:\Users\{user}\AppData\.pvplounge\logs\latest.log"
clientlist = [lunar_client, minecraft_client, badlion_client, pvplounge_client]

logfile = checkclient()

for i in playerlist:
    print(i)

with open(logfile) as f:
    currentline = len(f.readlines())  # finding the last line

while True:
    if os.stat(logfile).st_mtime > logfile_lastchanged:
        with open(logfile) as f:
            length = len(f.readlines())
        for line in range(currentline, length):
            with open(logfile) as f:
                lastline = f.readlines()[line]
            logfile_lastchanged = os.stat(logfile).st_mtime
            currentline = line + 1
            if lastline[11:30] != '[Client thread/INFO':
                break
            if lastline[40:47] == '§9Party' and '!bald' in lastline:  # legacy code
                if '!bald overall' in lastline:
                    overallprint()

                elif '!bald list' in lastline:
                    print(' ')
                    print('Playerlist:')
                    for i in playerlist:
                        print(i)                                      # not legacy anymore

            s = lastline.split()

            if len(playerlist) != 0:
                if lastline[-12:-1] == 'FINAL KILL!':
                    for player in playerlist:
                        if f'{player}' in lastline:
                            if f'{player}' != s[3]:
                                a = playerlist.index(f'{player}')
                                totalstats[a][1] += 1
                                printer(player)
                            else:
                                totalstats[playerlist.index(
                                    f'{player}')][2] += 1
                                printer(player)

            _s = s[3:]
            for i in _s:
                if i[0] != '[' and i[-1] != ']':
                    s.append(i)

            if len(s) == 4:
                # player joins the party
                if s[1] == 'joined' and s[3] == 'party.':
                    addplayer(s[0])
                # you leave the party
                if s[0] == 'You' and s[1] == 'left':
                    totalstats = totalstats[0]

            if len(s) == 5:
                # player leaves the party
                if s[2] == 'left' and s[4] == 'party.':
                    removeplayer(s[0])
                # you joined someone else's party
                elif s[0] == 'You' and s[3] == 'party!':
                    addplayer(s[2][:-2])
                # someone disbands the party
                elif s[1] == 'has' and s[2] == 'disbanded':
                    totalstats = totalstats[0]

            if len(s) == 7:
                # player gets removed from the party
                if s[1] == 'has' and s[3] == 'removed':
                    removeplayer(s[0])

            if len(s) == 14:
                # the party gets disbanded
                if s[1] == 'party' and s[3] == 'disbanded':
                    totalstats = totalstats[0]

            if s[0] == "You'll":
                s2 = lastline.split(':')
                namelist = []
                s = s2[3].split()
                if len(s) >= 4:
                    if s[1] == "You'll":
                        pl = s2[4].split(',')
                        for m in pl:
                            n = m.split()
                            ap = n[-1]
                            namelist.append(ap)
                        mtrequest(namelist)

    else:
        time.sleep(0.01)
