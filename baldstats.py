import time
import getpass
import os
import requests

user = (getpass.getuser())
a = '1.8'
logfile = r"C:\Users" + f"\{user}\.lunarclient\offline\{a}\logs\latest.log"
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
    if not player == None:
        displayname = player.get("displayname")
        return displayname
    else:
        if req.get('cause') == "You have already looked up this name recently":
            print('API request error, try again in a moment')
        else:
            print(f'ERROR: no player by the name of {ign} found')
        return 'error'


def addplayer(newplayer):
    if not newplayer in playerlist:
        playerlist.append(newplayer)
        nparray = [newplayer, 0, 0]
        totalstats.append(nparray)
        print(f'{newplayer} was added')


def removeplayer(kickedplayer):
    if kickedplayer in playerlist:
        del totalstats[playerlist.index(kickedplayer)]
        del playerlist[playerlist.index(kickedplayer)]
        print(f"{kickedplayer} was removed")
    else:
        print('ERROR: this player is not in the list')


def addnick(ign, nick):
    o = [ign, nick]
    nickedlist.append(o)
    nicks.append(nick)
    nickedplayers.append(ign)


def overallprint():
    print(' ')
    print('OVERALL STATS:')
    for i in totalstats:
        fdc = totalstats[playerlist.index(f'{i[0]}')][2]
        if fdc == 0:
            fdc = 1
        print(' ')
        print(f"{i[0]}'s fkdr =", round(totalstats[playerlist.index(f'{i[0]}')][1] / fdc, 2))
        print(f"{i[0]}'s final kills =", totalstats[playerlist.index(f'{i[0]}')][1])
        print(f"{i[0]}'s final deaths =", totalstats[playerlist.index(f'{i[0]}')][2])


ignnotentered = True
if not os.path.exists(cfgfile):
    while ignnotentered:
        ign = input('Enter your minecraft ign\n')
        ign = checkname(ign)
        if not ign == 'error':
            os.mkdir(r"C:\Users" + f"\{user}\Appdata\Roaming\Baldstats")
            with open(cfgfile, 'w') as cfg:
                cfg.write(f'Name = {ign}')
                ignnotentered = False
with open(cfgfile) as cfg:
    for cfgline in cfg:
        s = cfgline.split()
        addplayer(s[2])
        cfgplayer = s[2]
print(' ')
print('USAGE:\n')
print('All the commands need to be typed in the party chat in order for them to work')
print('!bald *argument*     Example: !bald add Usain_Bald\n')
print('argument list:')
print('add *nickname*  - adds a new player')
print('kick *nickname*  - removes a player')
print('overall  - prints session stats of everyone')
print('list  - prints current playerlist\n')
print('Playerlist:')
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
            if lastline[11:30] == '[main/INFO]: [CHAT]':
                if lastline[31:38] == '§9Party' and '!bald' in lastline:

                    if '!bald overall' in lastline:
                        overallprint()

                    elif '!bald list' in lastline:
                        print(' ')
                        print('Playerlist:')
                        for i in playerlist:
                            print(i)

                    elif '!bald nick' in lastline:
                        s = lastline.split()
                        if len(s) == 11:
                            nickedmvp = checkname(s[9])
                            if not nickedmvp == 'error':
                                if nickedmvp in playerlist:
                                    newplayer = s[10]
                                    if not newplayer in playerlist:
                                        playerlist.append(newplayer)
                                        nparray = [newplayer, 0, 0]
                                        totalstats.append(nparray)
                                        addnick(nickedmvp, newplayer)
                                        print(f"{nickedmvp}'s nick was set to {newplayer}" )
                                else:
                                    print(f'{nickedmvp} is not in the current party')

                elif not len(playerlist) == 0:
                    if lastline[-12:-1] == 'FINAL KILL!':
                        for player in playerlist:
                            s = lastline.split()
                            if f'{player}' in lastline:
                                if not f'{player}' == s[3]:
                                    if player in nicks:
                                        a = playerlist.index(f'{nickedplayers[nicks.index(player)]}')
                                    else:
                                        a = playerlist.index(f'{player}')
                                    totalstats[a][1] += 1
                                    printer(player)
                                else:
                                    totalstats[playerlist.index(f'{player}')][2] += 1
                                    printer(player)

                s = lastline.split()
                if 15 <= len(s) <= 17:  # you invite someone to the party
                    if s[5] == 'invited' and s[10] == 'party!':
                        addplayer(s[4])
                    elif s[5] == 'invited' and s[9] == 'party!':
                        addplayer(s[4])
                    elif s[4] == 'invited' and s[9] == 'party!':
                        addplayer(s[3])
                    elif s[4] == 'invited' and s[8] == 'party!':
                        addplayer(s[3])

                elif len(s) == 7:  # player joins the party
                    if s[4] == 'joined' and s[6] == 'party.':
                        addplayer(s[3])
                elif len(s) == 8:
                    if s[5] == 'joined' and s[6] == 'the' and s[7] == 'party.':
                        addplayer(s[4])

                if 8 <= len(s) <= 9:  # player leaves the party
                    if s[5] == 'left' and s[7] == 'party.':
                        removeplayer(s[3])
                    elif s[6] == 'left' and s[7] == 'the':
                        removeplayer(s[4])

                elif 10 <= len(s) <= 11:  # player gets removed from the party
                    if s[4] == 'has' and s[6] == 'removed':
                        removeplayer(s[3])
                    elif s[5] == 'has' and s[7] == 'removed':
                        removeplayer(s[4])
                if len(s) == 8:  # you join someone else's party
                    if s[3] == 'You' and s[7] == 'party!':
                        addplayer(s[6][:-2])
                elif len(s) == 9:
                    if s[3] == 'You' and s[8] == 'party!':
                        addplayer(s[7][:-2])
                s2 = lastline.split(':')
                if len(s2) == 5:
                    s = s2[3].split()
                    if len(s) >= 4:
                        if s[1] == "You'll":
                            pl = s2[4].split(',')
                            for m in pl:
                                n = m.split()
                                ap = n[-1]
                                addplayer(ap)
                if len(s) == 16:
                    if s[4] == 'party' and s[6] == 'disbanded':
                        if not len(playerlist) == 1:
                            for i in playerlist:
                                if not i == cfgplayer:
                                    removeplayer(i)
                            print('The party was disbanded')
                            overallprint()
                elif len(s) == 12:
                    if s[4] == 'party' and s[6] == 'disbanded':
                        if not len(playerlist) == 1:
                            for i in playerlist:
                                if not i == cfgplayer:
                                    removeplayer(i)
                            print('The party was disbanded')
                            overallprint()
                if len(s) == 7:
                    if s[3] == 'You' and s[4] == 'left':
                        for i in playerlist:
                            if not i == cfgplayer:
                                removeplayer(i)
                        print('you left the party')
                        overallprint()
            currentline = line + 1

        logfile_lastchanged = os.stat(logfile).st_mtime
    else:
        time.sleep(0.02)