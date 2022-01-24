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
logfile = ''
logfile_lastchanged = 0
currentline = 0
cd = 0
session_starttime = ''
stats_before = []
stats_after = []
APIkey = ''
baldstatsmode = ''
user_ign = ''
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
            if not session_isstarted:
                with open(cfgfile) as cfg:
                    for cfgline in cfg:
                        s = cfgline.split('=')
                        if s[0] == 'Name':
                            uuid_req = s[2].strip()
            else:
                uuid_req = totalstats[playerlist.index(name.strip())][4]
            url = f"https://api.hypixel.net/player?key={APIkey}&uuid={uuid_req}"
            req = requests.get(url).json()
            req_player = req.get('player')
            if req_player is not None:
                a = getbwstats(req_player)
                return a
        except Exception:
            print(f'Failed to make a request for {name}')


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
        p = getstats(newplayer)
        playerlist.append(newplayer)
        totalstats.append(p)
        if session_isstarted:
            player_join_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
            x = [i for i in p]
            x.append(player_join_time)
            stats_before.append(x)
        print(f'{newplayer} was added')
        print(totalstats)
        print(playerlist)


def removeplayer(kickedplayer):
    player_leave_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    kickedplayer = kickedplayer.strip()
    if kickedplayer in playerlist:
        if kickedplayer in [element for a_list in stats_before for element in a_list]:
            kickedplayer_stats_after = getstats(kickedplayer)
            kickedplayer_stats_after.append(player_leave_time)
            stats_after.append(kickedplayer_stats_after)
        del totalstats[playerlist.index(kickedplayer)]
        del playerlist[playerlist.index(kickedplayer)]
        print(f"{kickedplayer} was removed")
    else:
        print(f'ERROR: {kickedplayer} is not in the list')


def disband_party():
    global totalstats
    global playerlist
    player_leave_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    for sa_player in playerlist:
        if sa_player[0] != user_ign:
            kickedplayer_stats_after = getstats(sa_player[0])
            kickedplayer_stats_after.append(player_leave_time)
            stats_after.append(kickedplayer_stats_after)
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


def get_name():
    global totalstats
    global user_ign
    if os.path.exists(cfgfile):
        with open(cfgfile) as cfg:
            ignentered = False
            for cfgline in cfg:
                s = cfgline.split('=')
                if s[0] == 'Name':
                    ignentered = True
    while not ignentered:
        ign = input('Enter your minecraft nickname' + '\n')
        a = checkname(ign)
        ign = a[0]
        uuid = a[1]
        if ign != "":
            with open(cfgfile, 'a+') as cfg:
                cfg.write(f'Name={ign}={uuid}' + '\n')
                ignentered = True

    with open(cfgfile) as cfg:
        for cfgline in cfg:
            s = cfgline.split('=')
            if s[0] == 'Name':
                addplayer(s[1].strip())
                user_ign = s[1].strip()


def get_client():
    global logfile
    global clientlist
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


def party_adjust(party_array):
    global party_arr
    print(party_array)
    party_members = []
    for i in range(len(party_array)):
        if party_array[i] == '?':
            party_members.append(party_array[i - 1])
    if not sorted(playerlist) == sorted(party_members):
        for elem in party_members:
            if elem not in playerlist:
                addplayer(elem)
        for elem in playerlist:
            if elem not in party_members:
                removeplayer(elem)
    party_arr = []


def startsession():
    global session_starttime
    global stats_before
    global session_isstarted
    global totalstats
    session_starttime = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    for elem in totalstats:
        bef = [i for i in elem]
        bef.append(session_starttime)
        stats_before.append(bef)
    session_isstarted = True
    print('The session was started')
    print(f'Time = {session_starttime}')
    print(stats_before)


def endsession():
    session_endtime = player_leave_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    for sa_player in totalstats:
        kickedplayer_stats_after = getstats(sa_player[0])
        kickedplayer_stats_after.append(player_leave_time)
        stats_after.append(kickedplayer_stats_after)
    with open(statsfile, 'a+') as ss:
        ss.write(f'SESSION STARTED {session_starttime}' + '\n')
    for sa in stats_after:
        _ind = 20
        for sb in stats_before:
            if sa[0] == sb[0]:
                _ind = stats_before.index(sb)
                break
        sa_ign = sa[0]
        sa_final_kills = sa[2] - stats_before[_ind][2]
        sa_final_deaths = sa[3] - stats_before[_ind][3]
        if sa_final_deaths == 0:
            sa_fkdr = sa_final_kills
        else:
            sa_fkdr = round(sa_final_kills / sa_final_deaths, 2)
        sa_level_progress = sa[1] - stats_before[_ind][1]
        sa_xp_progress = sa[5] - stats_before[_ind][5]
        sa_join_time = stats_before[_ind][6]
        sa_leave_time = sa[6]
        with open(statsfile, 'a+') as ss:
            ss.write(
                f'{sa_ign} {sa_final_kills} {sa_final_deaths} {sa_fkdr} {sa_level_progress} {sa_xp_progress} {sa_join_time} {sa_leave_time}' + '\n')
    with open(statsfile, 'a+') as ss:
        ss.write(f'SESSION ENDED {session_endtime}' + '\n')
        ss.write('\n')


get_api_key()
get_name()
get_client()
choosemode()
remembermode()
# startsession()

for i in playerlist:
    print('Current party:')
    print(i)
with open(logfile) as f:
    currentline = len(f.readlines())  # finding the last line
session_is_over = False
party_check = False
party_arr = []
while not session_is_over:
    if os.stat(logfile).st_mtime > logfile_lastchanged:
        with open(logfile) as f:
            length = len(f.readlines())
        for line in range(currentline, length):
            with open(logfile) as f:
                lastline = f.readlines()[line].strip()
            logfile_lastchanged = os.stat(logfile).st_mtime
            currentline = line + 1

            if lastline == 'close_program':  # nado pomenyat na zakrytie programmy kogda budet gui
                if session_isstarted:
                    endsession()
                    session_is_over = True
                    break

            if lastline[11:31] == '[Client thread/INFO]':
                s = lastline.split()[4:]
                len_s = len(s)

                if s == ['Protect', 'your', 'bed', 'and', 'destroy', 'the', 'enemy', 'beds.']:
                    if not session_isstarted:
                        startsession()
                if party_check:
                    if len_s > 0:
                        if not s[0] == '-----------------------------':
                            for n in s:
                                party_arr.append(n)
                        else:
                            party_check = False
                            party_adjust(party_arr)
                if len_s > 1:
                    if s[0] == 'Party' and s[1] == 'Members':
                        party_check = True
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
                if session_isstarted:
                    if baldstatsmode == 'logfile':
                        if lastline[-11:] == 'FINAL KILL!':
                            for player in playerlist:
                                if player in lastline:
                                    a = playerlist.index(player)
                                    if player != s[0]:
                                        totalstats[a][2] += 1
                                    else:
                                        totalstats[a][3] += 1
                                    print(playerlist)
                                    print(stats_before)
                                    print(totalstats)
                                    print(player)
                                    overallprint()
                    elif baldstatsmode == 'api':
                        if cd <= time.time() - 30:
                            cd = time.time()
                            for i in playerlist:
                                getstats(i)
                                overallprint()

    else:
        time.sleep(0.1)
