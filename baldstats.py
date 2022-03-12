import time
import getpass
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from threading import Thread


class Communicate(QObject):
    process_logfile_line = pyqtSignal()
    update_table = pyqtSignal()


class Frame(QWidget):
    def __init__(self):
        super().__init__()
        # TODO: API new (for first-time users)
        # TODO: window close

        self.setWindowTitle("BaldStats testing")
        self.setMinimumSize(1000, 600)
        self.menu_bar = QMenuBar()
        self.settings_menu = QMenu("&Settings", self)

        self.stats_history_menu = QMenu("St&ats history", self)
        self.help_menu = QMenu("&Help", self)
        self.menu_bar.addMenu(self.settings_menu)
        self.menu_bar.addMenu(self.stats_history_menu)
        self.menu_bar.addMenu(self.help_menu)
        self.menu_bar.setDisabled(True)

        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        # TODO: remove old_tab
        self.old_tab = QWidget()
        self.session_stats_tab = QWidget()
        self.overall_stats_tab = QWidget()
        self.game_stats_tab = QWidget()
        self.overlay_stats_tab = QWidget()

        self.session_stats_tab_layout = QVBoxLayout(self.session_stats_tab)
        self.overall_stats_tab_layout = QVBoxLayout(self.overall_stats_tab)
        self.session_stats_table = QTableWidget()
        self.overall_stats_table = QTableWidget()
        self.session_stats_tab_layout.addWidget(self.session_stats_table)
        self.overall_stats_tab_layout.addWidget(self.overall_stats_table)
        self.session_stats_table.setColumnCount(8)
        self.overall_stats_table.setColumnCount(9)
        self.session_stats_table.setHorizontalHeaderLabels(
            ["Name", "Final kills", "Final deaths", "FKDR", "Wins", "Losses", "WLR", "Void deaths"])
        self.overall_stats_table.setHorizontalHeaderLabels(
            ["Name", "Stars", "Final kills", "Final deaths", "FKDR", "Wins", "Losses", "WLR", "BBLR"])

        self.tabs.addTab(self.old_tab, "Old tab")
        self.tabs.addTab(self.session_stats_tab, "Session stats")
        self.tabs.addTab(self.overall_stats_tab, "Overall stats")
        self.tabs.addTab(self.game_stats_tab, "Game stats")
        self.tabs.addTab(self.overlay_stats_tab, "Overlay stats")
        # TODO: less importans tabs
        self.tabs.setTabEnabled(3, False)
        self.tabs.setTabEnabled(4, False)

        self.main_layout.setMenuBar(self.menu_bar)
        self.main_layout.addWidget(self.tabs)
        self.show()
        print('UI init completed')

        ####################

        # TODO: remove self.table
        self.table = QTableWidget(self.old_tab)
        self.table.move(0, 0)
        self.table.setMinimumSize(600, 400)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Level", "FKDR", "Final kills", "Final deaths"])

        self.user = (getpass.getuser())
        # BEFORE_COMMIT uncomment
        self.cfg_file = f"C:/Users/{self.user}/Appdata/Roaming/Baldstats/settings.cfg"
        self.stats_file = f"C:/Users/{self.user}/Appdata/Roaming/Baldstats/session_stats.txt"
        # self.cfg_file = f"./settings.cfg"
        # self.stats_file = f"./session_stats.txt"

        # self.API_key = "f57c9f4a-175b-430c-a261-d8c199abd927"
        self.party_members = []
        self.party_stats = []
        self.party_stats_last = []
        self.log_file = ''
        self.log_file_last_changed = 0
        self.current_line = 0
        self.cd = 0
        self.session_start_time = ''
        self.stats_before = []
        self.stats_after = []
        self.API_key = ''
        self.baldstats_mode = ''
        self.user_ign = ''
        self.client_list = []
        self.mode_remembered = False
        self.session_is_started = False
        self.last_thread_line = ""
        self.events = []

        # BEFORE_COMMIT uncomment
        if not os.path.exists(f"C:/Users/{self.user}/Appdata/Roaming/Baldstats"):
            os.mkdir(f"C:/Users/{self.user}/Appdata/Roaming/Baldstats")

        self.get_api_key()
        self.get_name()
        self.get_client()
        self.choose_mode()
        self.remember_mode()

        for i in self.party_members:
            print('Current party:')
            print(i)

        with open(self.log_file) as f:
            self.current_line = len(f.readlines())  # finding the last line
        self.log_file_last_changed = os.stat(self.log_file).st_mtime

        self.session_is_over = False
        self.party_check = False
        self.game_ended_check = False
        self.party_arr = []

        # self.main_cycle()

        # TODO: fix AttributeError: 'Frame' object has no attribute 'logfile_thread'
        self.thread_running = True
        self.signal = Communicate()
        self.signal.process_logfile_line.connect(self.main_cycle)
        self.logfile_thread = Thread(target=self.watch_logs)
        self.logfile_thread.start()

        self.table_thread = Thread(target=self.update_table)
        self.table_thread.start()

    def update_table(self):
        while True:
            if len(self.party_stats) == len(self.party_stats_last):
                for i in range(len(self.party_stats)):
                    for j in range(len(self.party_stats_last[i])):
                        if self.party_stats[i][j] != self.party_stats_last[i][j]:
                            print(
                                i, j, self.party_stats[i][j], self.party_stats_last[i][j])
                            self.overall_stats_table.setItem(
                                i, j, QTableWidgetItem(str(self.party_stats[i][j])))

            self.party_stats_last = [i[:] for i in self.party_stats]
            time.sleep(0.1)

    def ui_show_settings_dialog(self):
        dialog = QDialog()
        button = QPushButton("Press me!", dialog)
        dialog.setWindowTitle("Settings dialog")
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()

    def print_stats(self):  # nado ubrat' kogda gui budet
        for current_player in self.party_stats:
            ps_index = sb_index = 'wrong index'
            session_displayname = current_player[0]
            for elem in self.stats_before:
                if elem[0] == current_player[0]:
                    sb_index = self.stats_before.index(elem)
            for elem in self.party_stats:
                if elem[0] == current_player[0]:
                    ps_index = self.party_stats.index(elem)
            session_bedwars_level = self.party_stats[ps_index][1] - \
                self.stats_before[sb_index][1]
            session_exp_progress = self.party_stats[ps_index][5] - \
                self.stats_before[sb_index][5]
            session_final_kills = self.party_stats[ps_index][2] - \
                self.stats_before[sb_index][2]
            session_final_deaths = self.party_stats[ps_index][3] - \
                self.stats_before[sb_index][3]
            if session_final_deaths == 0:
                session_final_deaths = 1
            print(' ')
            if self.baldstats_mode == 'api':
                print(f"{session_displayname}'s level progress =",
                      session_exp_progress)
                print(
                    f"{session_displayname} has gained {session_bedwars_level} levels this session")
            print(f"{session_displayname}'s fkdr =", round(
                session_final_kills / session_final_deaths, 2))
            print(f"{session_displayname}'s final kills =", session_final_kills)

    def check_name(self, ign):  # NEW
        url = f"https://api.hypixel.net/player?key={self.API_key}&name={ign}"
        req = requests.get(url).json()
        cn_player = req.get('player')
        if cn_player is not None:
            return self.get_bw_stats(cn_player)
        else:
            if req.get('cause') == "You have already looked up this name recently":
                print('API request error, try again in a moment')
            else:
                print(f'ERROR: no player by the name of {ign} found')
            return ""

    def get_bw_stats(self, req_player):
        req_displayname = req_player.get('displayname')
        req_uuid = req_player.get('uuid')
        req_achievements = req_player.get('achievements')
        req_bedwars_level = req_achievements.get('bedwars_level')
        req_stats = req_player.get('stats')
        req_bedwars = req_stats.get('Bedwars')
        req_xp = req_bedwars.get('Experience')
        req_final_kills = req_bedwars.get('final_kills_bedwars')
        req_beds_broken = req_bedwars.get('beds_broken_bedwars')
        if req_beds_broken is None:
            req_beds_broken = 0
        req_beds_lost = req_bedwars.get('beds_lost_bedwars')
        if req_beds_lost is None or req_beds_lost == 0:
            req_beds_lost = 1
        if req_final_kills is None:
            req_final_kills = 0
        req_final_deaths = req_bedwars.get('final_deaths_bedwars')
        if req_final_deaths is None:
            req_final_deaths = 1
        return [req_displayname, req_bedwars_level, req_final_kills, req_final_deaths, req_uuid, req_xp, 0,
                req_beds_broken, req_beds_lost]

    def get_stats_name(self, name):  # NEW
        name = name.strip()
        url = f"https://api.hypixel.net/player?key={self.API_key}&name={name}"
        req = requests.get(url).json()
        req_player = req.get('player')
        if req_player is not None:
            return self.get_bw_stats(req_player)

    # WHERE last_thread_line

    def get_stats_uuid(self, uuid):  # NEW
        url = f"https://api.hypixel.net/player?key={self.API_key}&uuid={uuid}"
        req = requests.get(url).json()
        req_player = req.get('player')
        if req_player is not None:
            return self.get_bw_stats(req_player)

    def mt_request(self, names):
        with ThreadPoolExecutor(80) as executor:
            for name in names:
                executor.submit(self.add_player, name)

    def add_player(self, new_player):
        new_player = new_player.strip()
        if len(new_player) > 16:  # checking whether it is an ign or a uuid
            new_player_stats = self.get_stats_uuid(new_player)
            new_player = new_player_stats[0]
        else:
            new_player_stats = self.get_stats_name(new_player)
            new_player = new_player_stats[0]

        if new_player not in self.party_members:
            # self.party_members.append(new_player)
            # playerlist sorting:
            pos = -1
            for i in range(len(self.party_stats)):
                if self.party_stats[i][1] < new_player_stats[1]:
                    pos = i
                    break

            if pos == -1:
                pos = len(self.party_members)

            self.party_members.append("")
            self.party_stats.append([])

            cur_player, cur_stats = new_player, new_player_stats
            for i in range(pos, len(self.party_members)):
                cur_player, self.party_members[i] = self.party_members[i], cur_player
                cur_stats, self.party_stats[i] = self.party_stats[i], cur_stats

            # GUI table updating:
            # if pos == -1:
            #     pos = self.table.rowCount()

            self.overall_stats_table.insertRow(pos)
            self.overall_stats_table.setItem(
                pos, 0, QTableWidgetItem(new_player_stats[0]))
            self.overall_stats_table.setItem(
                pos, 1, QTableWidgetItem(str(new_player_stats[1])))
            self.overall_stats_table.setItem(
                pos, 2, QTableWidgetItem(str(new_player_stats[2])))
            self.overall_stats_table.setItem(
                pos, 3, QTableWidgetItem(str(new_player_stats[3])))
            self.overall_stats_table.setItem(pos, 4, QTableWidgetItem(
                str(round(new_player_stats[2] / new_player_stats[3], 3))))
            self.overall_stats_table.setItem(
                pos, 5, QTableWidgetItem("no data"))
            self.overall_stats_table.setItem(
                pos, 6, QTableWidgetItem("no data"))
            self.overall_stats_table.setItem(
                pos, 7, QTableWidgetItem("now dta"))
            self.overall_stats_table.setItem(pos, 8, QTableWidgetItem(
                str(round(new_player_stats[7] / new_player_stats[8], 3))))

            if self.session_is_started:
                player_join_time = str(datetime.now())[
                    :10] + '_' + str(datetime.now())[11:16]
                x = [i for i in new_player_stats]
                x.append(player_join_time)
                self.stats_before.append(x)

            print(f'{new_player} was added')
            print(self.party_stats)
            print(self.party_members)

    def remove_player(self, kicked_player):
        player_leave_time = str(datetime.now())[
            :10] + '_' + str(datetime.now())[11:16]
        kicked_player = kicked_player.strip()
        if kicked_player in self.party_members:
            if kicked_player in [element for a_list in self.stats_before for element in a_list]:
                # kicked_player_stats_after = self.get_stats(kicked_player)
                ps_index = 'wrong index'
                for elem in self.party_stats:
                    if elem[0] == kicked_player:
                        ps_index = self.party_stats.index(elem)
                kicked_player_stats_after = self.get_stats_uuid(
                    self.party_stats[ps_index][4])
                kicked_player_stats_after.append(player_leave_time)
                self.stats_after.append(kicked_player_stats_after)

            self.overall_stats_table.removeRow(
                self.party_members.index(kicked_player))
            del self.party_stats[self.party_members.index(kicked_player)]
            del self.party_members[self.party_members.index(kicked_player)]
            print(f"{kicked_player} was removed")
        else:
            print(f'ERROR: {kicked_player} is not in the list')

    def disband_party(self):
        player_leave_time = str(datetime.now())[
            :10] + '_' + str(datetime.now())[11:16]
        if self.party_members != [self.user_ign]:
            print('the party was disbanded')
        for sa_player in self.party_members:
            if sa_player != self.user_ign:
                ps_index = 'wrong index'
                for elem in self.party_stats:
                    if elem[0] == sa_player:
                        ps_index = self.party_stats.index(elem)
                kicked_player_stats_after = self.get_stats_uuid(
                    self.party_stats[ps_index][4])
                kicked_player_stats_after.append(player_leave_time)
                self.stats_after.append(kicked_player_stats_after)

        self.overall_stats_table.clear()
        self.overall_stats_table.setRowCount(1)

        for i in self.party_stats:
            if i[0] == self.user_ign:
                self.party_stats = i[0]
                break

        self.party_members = [self.user_ign]

    def check_client(self):
        # # BEFORE_COMMIT uncomment
        # return "./latest.log"
        client = 0
        edit_last_changed = 0
        for i in self.client_list:
            if os.path.exists(i):
                if os.stat(i).st_mtime > edit_last_changed:
                    edit_last_changed = os.stat(i).st_mtime
                    client = i
        if client != 0:
            return client
        else:
            print("You don't have minecraft installed")

    def choose_mode(self):
        self.baldstats_mode = False
        self.mode_remembered = False
        if os.path.exists(self.cfg_file):
            with open(self.cfg_file) as cfg:
                for cfg_line in cfg:
                    s = cfg_line.split('=')
                    if s[0] == 'remember_mode':
                        self.mode_remembered = True
                        if s[1].strip() == 'log_file':
                            self.baldstats_mode = 'log_file'
                        elif s[1].strip() == 'api':
                            self.baldstats_mode = 'api'
        if not self.baldstats_mode:
            print('CHOOSE BALDSTATS MODE')
            print(
                'Type 1 to get stats from the log file (updates in real time, unable to track stats of nicked players)')
            print('Type 2 to get stats from the API (updates once every 30 seconds, tracks stats of nicked players)')
            m = int(input())
            if m == 1:
                self.baldstats_mode = 'log_file'
            elif m == 2:
                self.baldstats_mode = 'api'
            else:
                raise SystemError

    def remember_mode(self):
        if not self.mode_remembered:
            print('Do you want to remember your choice?')
            print('y - yes')
            print('n - no')
            m = input()
            if m == 'y':
                with open(self.cfg_file, 'a+') as cfg:
                    cfg.write(
                        f'remember_mode={self.baldstats_mode}' + '\n')

    def get_api_key(self):
        apikey = False
        api_key_check = False
        if os.path.exists(self.cfg_file):
            with open(self.cfg_file) as cfg:
                for cfg_line in cfg:
                    s = cfg_line.split('=')
                    if s[0] == 'self.API_key':
                        self.API_key = s[1].strip()
                        while not apikey:
                            req_link = f'https://api.hypixel.net/player?key={self.API_key}'
                            if requests.get(req_link) == '<Response [403]>':
                                print('Invalid API key, try again')
                                self.API_key = input()
                            else:
                                apikey = True
        if not apikey:
            print(
                'Enter your hypixel API key (you can get it by using /api new on the server)')
            while not api_key_check:
                self.API_key = input()
                req_link = f'https://api.hypixel.net/player?key={self.API_key}'
                if requests.get(req_link) == '<Response [403]>':
                    print('Invalid API key, try again')
                else:
                    with open(self.cfg_file, 'a+') as cfg:
                        cfg.write(f'self.API_key={self.API_key}' + '\n')
                    api_key_check = True

    def get_name(self):
        if os.path.exists(self.cfg_file):
            with open(self.cfg_file) as cfg:
                ign_entered = False
                for cfg_line in cfg:
                    s = cfg_line.split('=')
                    if s[0] == 'Name':
                        ign_entered = True
        while not ign_entered:
            ign = input('Enter your minecraft nickname' + '\n')
            a = self.check_name(ign)
            if a != "":
                ign = a[0]
                uuid = a[4]
                self.party_members.append(ign)
                self.party_stats.append(a)
                with open(self.cfg_file, 'a+') as cfg:
                    cfg.write(f'Name={ign}={uuid}' + '\n')
                    ign_entered = True

        with open(self.cfg_file) as cfg:
            for cfg_line in cfg:
                s = cfg_line.split('=')
                if s[0] == 'Name':
                    self.add_player(s[2].strip())
                    if self.party_stats == [None]:
                        print(
                            f'ERROR: Unable to get stats of {s[1].strip()}, try restarting the program')
                    else:
                        self.user_ign = self.party_members[0]

    def get_client(self):
        lunar_client = f"C:/Users/{self.user}/.lunarclient/offline/1.8/logs/latest.log"
        minecraft_client = f"C:/Users/{self.user}/AppData/Roaming/.minecraft/logs/latest.log"
        badlion_client = f"C:/Users/{self.user}/AppData/Roaming/.minecraft/logs/blclient/chat/latest.log"
        pvplounge_client = f"C:/Users/{self.user}/AppData/.pvplounge/logs/latest.log"

        self.client_list = [lunar_client, minecraft_client,
                            badlion_client, pvplounge_client]
        self.log_file = self.check_client()

        if self.log_file == badlion_client:
            print('Linked to Badlion Client')
        elif self.log_file == minecraft_client:
            print('Linked to the Official Launcher')
        elif self.log_file == lunar_client:
            print('Linked to Lunar Client')
        elif self.log_file == pvplounge_client:
            print('Linked to PVPLounge Client')
        else:
            print("Linked to custom client")

    def party_adjust(self, party_array):
        print(party_array)
        adj_party_members = []
        for i in range(len(party_array)):
            if party_array[i] == '?':
                adj_party_members.append(party_array[i - 1])
        if not sorted(self.party_members) == sorted(adj_party_members):
            for elem in adj_party_members:
                if elem not in self.party_members:
                    self.add_player(elem)
            for elem in self.party_members:
                if elem not in adj_party_members:
                    self.remove_player(elem)
        self.party_arr = []

    def start_session(self):
        self.session_start_time = str(datetime.now())[
            :10] + '_' + str(datetime.now())[11:16]
        for elem in self.party_stats:
            bef = [i for i in elem]
            bef.append(self.session_start_time)
            self.stats_before.append(bef)
        self.session_is_started = True
        print('The session was started')
        print(f'Time = {self.session_start_time}')
        print(self.stats_before)

    def end_session(self):
        session_end_time = player_leave_time = str(
            datetime.now())[:10] + '_' + str(datetime.now())[11:16]
        for sa_player in self.party_stats:
            kicked_player_stats_after = self.get_stats_uuid(sa_player[4])
            kicked_player_stats_after.append(player_leave_time)
            self.stats_after.append(kicked_player_stats_after)
        with open(self.stats_file, 'a+') as ss:
            ss.write(f'SESSION STARTED {self.session_start_time}' + '\n')
        for sa in self.stats_after:
            _ind = "wrong index"
            for sb in self.stats_before:
                if sa[0] == sb[0]:
                    _ind = self.stats_before.index(sb)
                    break
            sa_ign = sa[0]
            sa_final_kills = sa[2] - self.stats_before[_ind][2]
            sa_final_deaths = sa[3] - self.stats_before[_ind][3]
            if sa_final_deaths == 0:
                sa_fkdr = sa_final_kills
            else:
                sa_fkdr = round(sa_final_kills / sa_final_deaths, 2)
            sa_level_progress = sa[1] - self.stats_before[_ind][1]
            sa_xp_progress = sa[5] - self.stats_before[_ind][5]
            sa_join_time = self.stats_before[_ind][6]
            sa_leave_time = sa[6]
            del self.stats_before[_ind]
            with open(self.stats_file, 'a+') as ss:
                ss.write(
                    f'{sa_ign} {sa_final_kills} {sa_final_deaths} {sa_fkdr} {sa_level_progress} {sa_xp_progress}'
                    f' {sa_join_time} {sa_leave_time}' + '\n')
        with open(self.stats_file, 'a+') as ss:
            ss.write('events: ')
        with open(self.stats_file, 'a+') as ss:
            for event in self.events:
                ss.write(f'{event[0]}; {event[1]}; {event[2]}, ')
        with open(self.stats_file, 'a+') as ss:
            ss.write(f'SESSION ENDED {session_end_time}' + '\n')
            ss.write('\n')

    def create_event(self, name, event):
        event_time = str(datetime.now())[:10] + \
            '_' + str(datetime.now())[11:19]
        single_event = [name, event, event_time]
        self.events.append(single_event)

    def watch_logs(self):
        while not self.session_is_over and self.thread_running:
            if os.stat(self.log_file).st_mtime > self.log_file_last_changed:
                with open(self.log_file) as f:
                    length = len(f.readlines())
                print(length)
                for line in range(self.current_line, length):
                    with open(self.log_file) as f:
                        last_line = f.readlines()[line].strip()
                    self.log_file_last_changed = os.stat(
                        self.log_file).st_mtime
                    self.current_line = line + 1

                    if last_line[11:31] == '[Client thread/INFO]':
                        self.last_thread_line = last_line
                        self.signal.process_logfile_line.emit()
            else:
                time.sleep(0.5)

    def main_cycle(self):
        last_line = self.last_thread_line
        if last_line[-1] == '.' or last_line[-1] == '!':  # unnecessary solution
            last_line = last_line[:-1]
        s = last_line.split()[4:]

        for i in range(len(s)):
            if s[i][0] == '[' and s[i][-1] == ']':
                del s[i]
                break

        if s == ['Protect', 'your', 'bed', 'and', 'destroy', 'the', 'enemy', 'beds']:
            if not self.session_is_started:
                self.start_session()
            self.create_event('event-', 'game_started')
        if self.party_check:
            if len(s) > 0:
                if not s[0] == '-----------------------------':
                    for n in s:
                        self.party_arr.append(n)
                else:
                    self.party_check = False
                    self.party_adjust(self.party_arr)
        if self.game_ended_check:
            if len(s) > 2:
                if s[1] == '-':
                    if s[2][:-1] in self.party_members:
                        self.create_event('event-', 'game_won')
                    else:
                        self.create_event('event-', 'game_lost')
                    self.game_ended_check = False
        if len(s) > 1:
            if s[0] == 'Party' and s[1] == 'Members':
                self.party_check = True
            elif s[1] == '????????????????????????????????????????????????????????????????':
                self.game_ended_check = True
        if len(s) == 4:
            # player joins the party (works)
            if s[1] == 'joined' and s[3] == 'party':
                self.add_player(s[0])
            # you leave the party (works)
            if s[0] == 'You' and s[1] == 'left':
                self.disband_party()
                print('You left the party')

        if len(s) == 5:
            # player leaves the party (works)
            if s[2] == 'left' and s[4] == 'party':
                self.remove_player(s[0])
            # you joined someone else's party (works)
            elif s[0] == 'You' and s[4] == 'party':
                self.disband_party()
                if s[3][-1] == "'":
                    self.add_player(s[3][:-1])
                else:
                    self.add_player(s[3][:-2])
            # someone disbands the party (should work)
            elif s[1] == 'has' and s[2] == 'disbanded':
                self.disband_party()

        if len(s) == 6:
            if s[0] == 'Your' and s[2] == 'API':
                with open(self.cfg_file) as cfg:
                    for cfg_line in cfg:
                        st = cfg_line.split('=')
                        if st[0] == 'API_KEY':
                            old_api = st[1].strip()
                self.API_key = s[5]
                with open(self.cfg_file, 'r') as f:
                    old_data = f.read()
                new_data = old_data.replace(f'{old_api}', f'{self.API_key}')
                with open(self.cfg_file, 'w') as f:
                    f.write(new_data)
                print('Your API key was updated')

        if len(s) == 7:
            # player gets removed from the party (should work)
            if s[1] == 'has' and s[3] == 'removed':
                self.remove_player(s[0])
            # the party is empty
            if s[0] == 'You' and s[2] == 'not' and s[6] == 'party':
                self.disband_party()

        if len(s) == 9:
            # player gets removed from the party (should work)
            if s[1] == 'was' and s[2] == 'removed':
                self.remove_player(s[0])

        if len(s) == 14:
            # the party gets disbanded (idk if it works)
            if s[1] == 'party' and s[3] == 'disbanded':
                self.disband_party()

        if len(s) > 0:
            if s[0] == "You'll":
                # You join a party with multiple players in it (works)
                s2 = last_line.split(':')
                namelist = []
                s = s2[3].split()
                if len(s) >= 4:
                    if s[1] == "You'll":
                        pl = s2[4].split(',')
                        for m in pl:
                            n = m.split()
                            ap = n[-1]
                            namelist.append(ap)
                        self.mt_request(namelist)
        if self.session_is_started:
            if self.baldstats_mode == 'log_file':
                if last_line[-10:] == 'FINAL KILL':
                    for player in self.party_members:
                        if player in last_line:
                            a = self.party_members.index(
                                player)
                            if player != s[0]:
                                self.party_stats[a][2] += 1
                            else:
                                self.party_stats[a][3] += 1
                            print(self.stats_before)
                            print(self.party_stats)
                            self.print_stats()
                if last_line[-18:] == 'fell into the void':
                    player = s[0]
                    if player in self.party_members:
                        for fv_player in self.party_stats:
                            if fv_player[0] == player:
                                fv_player[6] += 1
                                self.create_event(f'{player}', 'voided')
                if len(s) > 1:
                    if s[0] == 'BED' and s[1] == 'DESTROYED':
                        player = s[0]
                        if player in self.party_members:
                            for fv_player in self.party_stats:
                                if fv_player[0] == player:
                                    fv_player[7] += 1
                                    self.create_event(
                                        f'{player}', 'bed_broken')
                        if 'Your bed' in last_line:
                            self.create_event(f'{player}', 'bed_lost')
                            for fv_player in self.party_stats:
                                fv_player[8] += 1
            elif self.baldstats_mode == 'api':
                if self.cd <= time.time() - 8:
                    self.cd = time.time()
                    for i in range(len(self.party_stats)):
                        self.party_stats[i] = self.get_stats_uuid(
                            self.party_stats[i][4])
                    self.print_stats()

    def closeEvent(self, event):
        self.thread_running = False
        self.logfile_thread.join()
        if self.session_is_started:
            self.end_session()
            self.session_is_over = True
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    frame = Frame()
    # frame.show()
    sys.exit(app.exec_())
