import time
import getpass
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

user = (getpass.getuser())
cfg_file = f"C:/Users/{user}/Appdata/Roaming/Baldstats/settings.cfg"
stats_file = f"C:/Users/{user}/Appdata/Roaming/Baldstats/session_stats.txt"
# API_key = "f57c9f4a-175b-430c-a261-d8c199abd927"
party_members = []
party_stats = []
log_file = ''
log_file_last_changed = 0
current_line = 0
cd = 0
session_start_time = ''
stats_before = []
stats_after = []
API_key = ''
baldstats_mode = ''
user_ign = ''
client_list = []
mode_remembered = False
session_is_started = False

if not os.path.exists(f"C:/Users/{user}/Appdata/Roaming/Baldstats"):
    os.mkdir(f"C:/Users/{user}/Appdata/Roaming/Baldstats")


def print_stats():  # nado ubrat' kogda gui budet
    for current_player in party_stats:
        t_index = sb_index = 'wrong index'
        session_displayname = current_player[0]
        for elem in stats_before:
            if elem[0] == current_player[0]:
                sb_index = stats_before.index(elem)
        for elem in party_stats:
            if elem[0] == current_player[0]:
                t_index = party_stats.index(elem)
        session_bedwars_level = party_stats[t_index][1] - stats_before[sb_index][1]
        session_exp_progress = party_stats[t_index][5] - stats_before[sb_index][5]
        session_final_kills = party_stats[t_index][2] - stats_before[sb_index][2]
        session_final_deaths = party_stats[t_index][3] - stats_before[sb_index][3]
        if session_final_deaths == 0:
            session_final_deaths = 1
        print(' ')
        if baldstats_mode == 'api':
            print(f"{session_displayname}'s level progress =", session_exp_progress)
            print(f"{session_displayname} has gained {session_bedwars_level} levels this session")
        print(f"{session_displayname}'s fkdr =", round(session_final_kills / session_final_deaths, 2))
        print(f"{session_displayname}'s final kills =", session_final_kills)


'''def check_name(ign):
    url = f"https://api.hypixel.net/player?key={API_key}&name={ign}"
    req = requests.get(url).json()
    cn_player = req.get('player')
    if cn_player is not None:
        displayname = cn_player.get("displayname")
        uuid = cn_player.get("uuid")
        return [displayname, uuid]
    else:
        if req.get('cause') == "You have already looked up this name recently":
            print('API request error, try again in a moment')
        else:
            print(f'ERROR: no player by the name of {ign} found')
        return ""'''


def get_bw_stats(req_player):
    req_displayname = req_player.get('displayname')
    req_uuid = req_player.get('uuid')
    req_achievements = req_player.get('achievements')
    req_bedwars_level = req_achievements.get('bedwars_level')
    req_stats = req_player.get('stats')
    req_bedwars = req_stats.get('Bedwars')
    req_xp = req_bedwars.get('Experience')
    req_final_kills = req_bedwars.get('final_kills_bedwars')
    if req_final_kills is None:
        req_final_kills = 0
    req_final_deaths = req_bedwars.get('final_deaths_bedwars')
    if req_final_deaths is None:
        req_final_deaths = 1
    return [req_displayname, req_bedwars_level, req_final_kills, req_final_deaths, req_uuid, req_xp]


def get_stats(name):
    name = name.strip()
    url = f"https://api.hypixel.net/player?key={API_key}&name={name}"
    req = requests.get(url).json()
    req_player = req.get('player')
    if req_player is not None:
        h = get_bw_stats(req_player)
        print(h)
        return h
    else:
        try:
            if len(party_members) == 0:
                with open(cfg_file) as cfg:
                    for cfg_line in cfg:
                        c = cfg_line.split('=')
                        if s[0] == 'Name':
                            uuid_req = c[2].strip()
            else:
                t_index = 'wrong index'
                for elem in party_stats:
                    if elem[0] == name:
                        t_index = party_stats.index(elem)
                uuid_req = party_stats[t_index][4]
            url = f"https://api.hypixel.net/player?key={API_key}&uuid={uuid_req}"
            req = requests.get(url).json()
            req_player = req.get('player')
            if req_player is not None:
                return get_bw_stats(req_player)
        except Exception:
            print(f'Failed to make a request for {name}')


def mt_request(names):
    with ThreadPoolExecutor(80) as executor:
        for name in names:
            executor.submit(add_player, name)


def add_player(new_player):
    new_player = new_player.strip()
    if new_player not in party_members:
        p = get_stats(new_player)
        party_members.append(new_player)
        party_stats.append(p)
        if session_is_started:
            player_join_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
            x = [i for i in p]
            x.append(player_join_time)
            stats_before.append(x)
        print(f'{new_player} was added')
        print(party_stats)
        print(party_members)


def remove_player(kicked_player):
    player_leave_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    kicked_player = kicked_player.strip()
    if kicked_player in party_members:
        if kicked_player in [element for a_list in stats_before for element in a_list]:
            kicked_player_stats_after = get_stats(kicked_player)
            kicked_player_stats_after.append(player_leave_time)
            stats_after.append(kicked_player_stats_after)
        del party_stats[party_members.index(kicked_player)]
        del party_members[party_members.index(kicked_player)]
        print(f"{kicked_player} was removed")
    else:
        print(f'ERROR: {kicked_player} is not in the list')


def disband_party():
    global party_stats
    global party_members
    player_leave_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    for sa_player in party_members:
        if sa_player[0] != user_ign:
            kicked_player_stats_after = get_stats(sa_player[0])
            kicked_player_stats_after.append(player_leave_time)
            stats_after.append(kicked_player_stats_after)
    party_stats = [party_stats[0]]
    party_members = [party_members[0]]
    print('the party was disbanded')


def check_client():
    client = 0
    edit_last_changed = 0
    for i in client_list:
        if os.path.exists(i):
            if os.stat(i).st_mtime > edit_last_changed:
                edit_last_changed = os.stat(i).st_mtime
                client = i
    if client != 0:
        return client
    else:
        print("You don't have minecraft installed")


def choose_mode():
    global baldstats_mode
    global mode_remembered
    baldstats_mode = False
    mode_remembered = False
    if os.path.exists(cfg_file):
        with open(cfg_file) as cfg:
            for cfg_line in cfg:
                s = cfg_line.split('=')
                if s[0] == 'remember_mode':
                    mode_remembered = True
                    if s[1].strip() == 'log_file':
                        baldstats_mode = 'log_file'
                    elif s[1].strip() == 'api':
                        baldstats_mode = 'api'
    if not baldstats_mode:
        print('CHOOSE BALDSTATS MODE')
        print('Type 1 to get stats from the log file (updates in real time, unable to track stats of nicked players)')
        print('Type 2 to get stats from the API (updates once every 30 seconds, tracks stats of nicked players)')
        m = int(input())
        if m == 1:
            baldstats_mode = 'log_file'
        elif m == 2:
            baldstats_mode = 'api'
        else:
            raise SystemError


def remember_mode():
    global baldstats_mode
    global mode_remembered
    if not mode_remembered:
        print('Do you want to remember your choice?')
        print('y - yes')
        print('n - no')
        m = input()
        if m == 'y':
            with open(cfg_file, 'a+') as cfg:
                cfg.write(f'remember_mode={baldstats_mode}' + '\n')


def get_api_key():
    global API_key
    apikey = False
    api_key_check = False
    if os.path.exists(cfg_file):
        with open(cfg_file) as cfg:
            for cfg_line in cfg:
                s = cfg_line.split('=')
                if s[0] == 'API_KEY':
                    API_key = s[1].strip()
                    while not apikey:
                        req_link = f'https://api.hypixel.net/player?key={API_key}'
                        if requests.get(req_link) == '<Response [403]>':
                            print('Invalid API key, try again')
                            API_key = input()
                        else:
                            apikey = True
    if not apikey:
        print('Enter your hypixel API key (you can get it by using /api new on the server)')
        while not api_key_check:
            API_key = input()
            req_link = f'https://api.hypixel.net/player?key={API_key}'
            if requests.get(req_link) == '<Response [403]>':
                print('Invalid API key, try again')
            else:
                with open(cfg_file, 'a+') as cfg:
                    cfg.write(f'API_KEY={API_key}' + '\n')
                api_key_check = True


def get_name():
    global party_stats
    global user_ign
    if os.path.exists(cfg_file):
        with open(cfg_file) as cfg:
            ign_entered = False
            for cfg_line in cfg:
                s = cfg_line.split('=')
                if s[0] == 'Name':
                    ign_entered = True
    while not ign_entered:
        ign = input('Enter your minecraft nickname' + '\n')
        a = check_name(ign)
        ign = a[0]
        uuid = a[1]
        if ign != "":
            with open(cfg_file, 'a+') as cfg:
                cfg.write(f'Name={ign}={uuid}' + '\n')
                ign_entered = True

    with open(cfg_file) as cfg:
        for cfg_line in cfg:
            s = cfg_line.split('=')
            if s[0] == 'Name':
                add_player(s[1].strip())
                user_ign = s[1].strip()


def get_client():
    global log_file
    global client_list
    lunar_client = f"C:/Users/{user}/.lunarclient/offline/1.8/logs/latest.log"
    minecraft_client = f"C:/Users/{user}/AppData/Roaming/.minecraft/logs/latest.log"
    badlion_client = f"C:/Users/{user}/AppData/Roaming/.minecraft/logs/blclient/chat/latest.log"
    pvplounge_client = f"C:/Users/{user}/AppData/.pvplounge/logs/latest.log"

    client_list = [lunar_client, minecraft_client, badlion_client, pvplounge_client]
    log_file = check_client()

    if log_file == badlion_client:
        print('Linked to Badlion Client')
    elif log_file == minecraft_client:
        print('Linked to the Official Launcher')
    elif log_file == lunar_client:
        print('Linked to Lunar Client')
    elif log_file == pvplounge_client:
        print('Linked to PVPLounge Client')


def party_adjust(party_array):
    global party_arr
    print(party_array)
    adj_party_members = []
    for i in range(len(party_array)):
        if party_array[i] == '?':
            adj_party_members.append(party_array[i - 1])
    if not sorted(party_members) == sorted(adj_party_members):
        for elem in adj_party_members:
            if elem not in party_members:
                add_player(elem)
        for elem in party_members:
            if elem not in adj_party_members:
                remove_player(elem)
    party_arr = []


def start_session():
    global session_start_time
    global stats_before
    global session_is_started
    global party_stats
    session_start_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    for elem in party_stats:
        bef = [i for i in elem]
        bef.append(session_start_time)
        stats_before.append(bef)
    session_is_started = True
    print('The session was started')
    print(f'Time = {session_start_time}')
    print(stats_before)


def end_session():
    session_end_time = player_leave_time = str(datetime.now())[:10] + '_' + str(datetime.now())[11:16]
    for sa_player in party_stats:
        kicked_player_stats_after = get_stats(sa_player[0])
        kicked_player_stats_after.append(player_leave_time)
        stats_after.append(kicked_player_stats_after)
    with open(stats_file, 'a+') as ss:
        ss.write(f'SESSION STARTED {session_start_time}' + '\n')
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
        with open(stats_file, 'a+') as ss:
            ss.write(
                f'{sa_ign} {sa_final_kills} {sa_final_deaths} {sa_fkdr} {sa_level_progress} {sa_xp_progress} {sa_join_time} {sa_leave_time}' + '\n')
    with open(stats_file, 'a+') as ss:
        ss.write(f'SESSION ENDED {session_end_time}' + '\n')
        ss.write('\n')


get_api_key()
get_name()
get_client()
choose_mode()
remember_mode()
# start_session()

for i in party_members:
    print('Current party:')
    print(i)
with open(log_file) as f:
    current_line = len(f.readlines())  # finding the last line
session_is_over = False
party_check = False
party_arr = []
while not session_is_over:
    if os.stat(log_file).st_mtime > log_file_last_changed:
        with open(log_file) as f:
            length = len(f.readlines())
        for line in range(current_line, length):
            with open(log_file) as f:
                last_line = f.readlines()[line].strip()
            log_file_last_changed = os.stat(log_file).st_mtime
            current_line = line + 1

            if last_line == 'close_program':  # nado pomenyat na zakrytie programmy kogda budet gui
                if session_is_started:
                    end_session()
                    session_is_over = True
                    break

            if last_line[11:31] == '[Client thread/INFO]':
                s = last_line.split()[4:]
                len_s = len(s)

                if s == ['Protect', 'your', 'bed', 'and', 'destroy', 'the', 'enemy', 'beds.']:
                    if not session_is_started:
                        start_session()
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
                        add_player(s[0])
                    # you leave the party (works)
                    if s[0] == 'You' and s[1] == 'left':
                        disband_party()
                        print('You left the party')

                if len_s == 5:
                    # player leaves the party (works)
                    if s[2] == 'left' and s[4] == 'party.':
                        remove_player(s[0])
                    # you joined someone else's party (works)
                    elif s[0] == 'You' and s[4] == 'party!':
                        if s[3][-1] == "'":
                            add_player(s[3][:-1])
                        else:
                            add_player(s[3][:-2])
                    # someone disbands the party (should work)
                    elif s[1] == 'has' and s[2] == 'disbanded':
                        disband_party()

                if len_s == 7:
                    # player gets removed from the party (should work)
                    if s[1] == 'has' and s[3] == 'removed':
                        remove_player(s[0])
                    # the party is empty
                    if s[0] == 'You' and s[2] == 'not' and s[6] == 'party.':
                        disband_party()

                if len_s == 9:
                    # player gets removed from the party (should work)
                    if s[1] == 'was' and s[2] == 'removed':
                        remove_player(s[0])

                if len_s == 14:
                    # the party gets disbanded (idk if it works)
                    if s[1] == 'party' and s[3] == 'disbanded':
                        disband_party()
                if len_s > 0:
                    if s[0] == "You'll":
                        # You join a party with multiple players in it (works)
                        s2 = last_line.split(':')
                        namelist = []
                        s = s2[3].split()
                        if len_s >= 4:
                            if s[1] == "You'll":
                                pl = s2[4].split(',')
                                for m in pl:
                                    n = m.split()
                                    ap = n[-1]
                                    namelist.append(ap)
                                mt_request(namelist)
                if session_is_started:
                    if baldstats_mode == 'log_file':
                        if last_line[-11:] == 'FINAL KILL!':
                            for player in party_members:
                                if player in last_line:
                                    a = party_members.index(player)
                                    if player != s[0]:
                                        party_stats[a][2] += 1
                                    else:
                                        party_stats[a][3] += 1
                                    print(stats_before)
                                    print(party_stats)
                                    print_stats()
                    elif baldstats_mode == 'api':
                        print(time.time())
                        print(time.time() - 30)
                        if cd <= time.time() - 30:
                            cd = time.time()
                            for i in party_members:
                                get_stats(i)
                                print_stats()

    else:
        time.sleep(0.1)
