import time
import getpass
import os
import requests
from concurrent.futures import ThreadPoolExecutor
import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from threading import Thread


class Frame(QWidget):
    def __init__(self):
        super().__init__()
        # TODO: /api new (for first-time users)
        # TODO: the gui only updates when you switch to the tab
        # TODO: graphs and tables from session_stats.txt
        # TODO: overlay
        self.bool_debug_is_enabled = False  # for masochists (Linux users), True - Linux, False - Windows

        self.setWindowTitle("BaldStats Unreleased")
        self.setMinimumSize(1000, 600)
        self.menu_bar = QMenuBar()
        self.settings_menu = QMenu("&Settings", self)

        self.stats_history_menu = QMenu("&Stats history", self)
        self.help_menu = QMenu("&Help", self)
        self.menu_bar.addMenu(self.settings_menu)
        self.menu_bar.addMenu(self.stats_history_menu)
        self.menu_bar.addMenu(self.help_menu)
        self.menu_bar.setDisabled(True)

        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        self.session_stats_tab = QWidget()
        self.overall_stats_tab = QWidget()
        self.game_stats_tab = QWidget()
        self.overlay_stats_tab = QWidget()

        self.session_stats_tab_layout = QVBoxLayout(self.session_stats_tab)
        self.overall_stats_tab_layout = QVBoxLayout(self.overall_stats_tab)
        self.game_stats_tab_layout = QVBoxLayout(self.game_stats_tab)
        self.session_stats_table = QTableWidget()
        self.overall_stats_table = QTableWidget()
        self.game_stats_table = QTableWidget()
        self.session_stats_tab_layout.addWidget(self.session_stats_table)
        self.overall_stats_tab_layout.addWidget(self.overall_stats_table)
        self.game_stats_tab_layout.addWidget(self.game_stats_table)
        self.session_stats_table.setColumnCount(8)
        self.overall_stats_table.setColumnCount(9)
        self.game_stats_table.setColumnCount(6)
        self.session_stats_table.setHorizontalHeaderLabels(
            ["Name", "Final kills", "Final deaths", "FKDR", "Wins", "Losses", "WLR", "Void deaths"])
        self.overall_stats_table.setHorizontalHeaderLabels(
            ["Name", "Stars", "Final kills", "Final deaths", "FKDR", "Wins", "Losses", "WLR", "BBLR"])
        self.game_stats_table.setHorizontalHeaderLabels(
            ["Name", "Kills", "Deaths", "Final kills", "Beds broken", "Void deaths"])

        self.tabs.addTab(self.session_stats_tab, "Session stats")
        self.tabs.addTab(self.overall_stats_tab, "Overall stats")
        self.tabs.addTab(self.game_stats_tab, "Game stats")
        self.tabs.addTab(self.overlay_stats_tab, "Overlay")
        self.tabs.setTabEnabled(3, False)

        self.main_layout.setMenuBar(self.menu_bar)
        self.main_layout.addWidget(self.tabs)
        self.show()
        print('UI init completed')

        ####################

        self.user = (getpass.getuser())

        if self.bool_debug_is_enabled:
            self.cfg_file = f"./settings.cfg"
            self.stats_file = f"./session_stats.txt"
        else:
            self.cfg_file = f"C:/Users/{self.user}/Appdata/Roaming/Baldstats/settings.cfg"
            self.stats_file = f"C:/Users/{self.user}/Appdata/Roaming/Baldstats/session_stats.txt"

        # self.API_key = "f57c9f4a-175b-430c-a261-d8c199abd927"  # don't steal my api key pls
        self.party_members = []
        self.party_stats = []
        self.party_stats_last = []  # for threading and table updating
        self.log_file = ''  # a path to the logfile
        self.log_file_last_changed = 0  # time when logfile was last changed
        self.logfile_last_line = 0  # last processed logfile line
        self.cooldown = 0  # cooldown for the api mode
        self.session_start_time = ''
        self.game_stats = []  # stats of a single game
        self.game_stats_history = []
        self.stats_before = []  # stats of players when they join the party
        self.stats_after = []  # stats of players when they leave the party or when the session ends
        self.API_key = ''
        self.baldstats_mode = ''
        self.user_ign = ''  # in-game name of the user
        self.client_list = []  # list of minecraft clients
        self.mode_remembered = False
        self.session_is_started = False
        self.events = []  # list of in-game events (final kills/deaths, bed destructions, etc.)
        self.uuid_dict = {}  # uuids of every player who joined the party during a session)

        if not self.bool_debug_is_enabled and not os.path.exists(f"C:/Users/{self.user}/Appdata/Roaming/Baldstats"):
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
            self.logfile_last_line = len(f.readlines())  # finding the last line
        self.log_file_last_changed = os.stat(self.log_file).st_mtime

        self.session_is_over = False
        self.party_check = False  # a bunch of different checks
        self.game_ended_check = False
        self.party_arr = []  # for self.party_adjust()

        # TODO: fix AttributeError: 'Frame' object has no attribute 'logfile_thread'
        self.thread_running = True

        self.logfile_thread = Thread(target=self.watch_logs)
        self.logfile_thread.start()

        self.table_thread = Thread(target=self.ui_update_table)
        self.table_thread.start()

    def ui_make_table(self):
        for i in range(len(self.party_stats)):
            self.overall_stats_table.setItem(
                i, 0, QTableWidgetItem(str(self.party_stats[i][0])))
            self.overall_stats_table.setItem(
                i, 1, QTableWidgetItem(str(self.party_stats[i][1])))
            self.overall_stats_table.setItem(
                i, 2, QTableWidgetItem(str(self.party_stats[i][2])))
            self.overall_stats_table.setItem(
                i, 3, QTableWidgetItem(str(self.party_stats[i][3])))
            self.overall_stats_table.setItem(
                i, 4, QTableWidgetItem(str(round(self.party_stats[i][2] / self.party_stats[i][3], 3))))
            self.overall_stats_table.setItem(
                i, 5, QTableWidgetItem(str(self.party_stats[i][9])))
            self.overall_stats_table.setItem(
                i, 6, QTableWidgetItem(str(self.party_stats[i][10])))
            self.overall_stats_table.setItem(
                i, 7, QTableWidgetItem(str(round(self.party_stats[i][9] / self.party_stats[i][10], 3))))
            self.overall_stats_table.setItem(
                i, 8, QTableWidgetItem(str(round(self.party_stats[i][7] / self.party_stats[i][8], 3))))

            # filling session stats table
            if self.stats_before == []:
                self.stats_before = [i[:] for i in self.party_stats]
                self.stats_before.append('bebra')
            self.session_stats_table.setItem(
                i, 0, QTableWidgetItem(str(self.party_stats[i][0])))
            self.session_stats_table.setItem(
                i, 1, QTableWidgetItem(str(self.party_stats[i][2] - self.stats_before[i][2])))
            self.session_stats_table.setItem(
                i, 2, QTableWidgetItem(str(self.party_stats[i][3] - self.stats_before[i][3])))
            if self.party_stats[i][3] - self.stats_before[i][3] == 0:
                self.session_stats_table.setItem(
                    i, 3, QTableWidgetItem(str(round((self.party_stats[i][2] - self.stats_before[i][2])))))
            else:
                self.session_stats_table.setItem(
                    i, 3, QTableWidgetItem(str(round((self.party_stats[i][2] - self.stats_before[i][2]) /
                                                     (self.party_stats[i][3] - self.stats_before[i][3]), 3))))
            self.session_stats_table.setItem(
                i, 4, QTableWidgetItem(str(self.party_stats[i][9] - self.stats_before[i][9])))
            self.session_stats_table.setItem(
                i, 5, QTableWidgetItem(str(self.party_stats[i][10] - self.stats_before[i][10])))
            if self.party_stats[i][10] - self.stats_before[i][10] == 0:
                self.session_stats_table.setItem(
                    i, 6, QTableWidgetItem(str(round((self.party_stats[i][9] - self.stats_before[i][9])))))
            else:
                self.session_stats_table.setItem(
                    i, 6, QTableWidgetItem(str(round((self.party_stats[i][9] - self.stats_before[i][9]) /
                                                     (self.party_stats[i][10] - self.stats_before[i][10]), 3))))
            self.session_stats_table.setItem(
                i, 7, QTableWidgetItem(str(self.party_stats[i][6])))
            if len(self.stats_before) == 2 and self.stats_before[1] == 'bebra':
                self.stats_before = []
            self.game_stats_table.setItem(i, 0, QTableWidgetItem(str(self.party_stats[i][0])))
            self.game_stats_table.setItem(i, 1, QTableWidgetItem(str(self.party_stats[i][11] - self.game_stats[i][11])))
            self.game_stats_table.setItem(i, 2, QTableWidgetItem(str(self.party_stats[i][12] - self.game_stats[i][12])))
            self.game_stats_table.setItem(i, 3, QTableWidgetItem(str(self.party_stats[i][2] - self.game_stats[i][2])))
            self.game_stats_table.setItem(i, 4, QTableWidgetItem(str(self.party_stats[i][7] - self.game_stats[i][7])))
            self.game_stats_table.setItem(i, 5, QTableWidgetItem(str(self.party_stats[i][6] - self.game_stats[i][6])))

    def ui_update_table(self):
        while self.thread_running:
            if len(self.party_stats) == len(self.party_stats_last):
                if self.party_stats != self.party_stats_last:
                    self.ui_make_table()
            self.party_stats_last = [i[:] for i in self.party_stats]
            time.sleep(0.1)

    def ui_reset_game_stats_table(self):
        self.game_stats = []
        for i in self.party_stats:
            self.game_stats.append(i[:])
        self.game_stats_table.clear()
        self.game_stats_table.setRowCount(len(self.party_stats))
        self.game_stats_table.setHorizontalHeaderLabels(
            ["Name", "Kills", "Deaths", "Final kills", "Beds broken", "Void deaths"])
        for pos in range(len(self.party_stats)):
            self.game_stats_table.setItem(pos, 0, QTableWidgetItem(self.party_stats[pos][0]))
            for i in range(1, 6):
                self.game_stats_table.setItem(pos, i, QTableWidgetItem("0"))

    def ui_show_settings_dialog(self):
        dialog = QDialog()
        button = QPushButton("Press me!", dialog)
        dialog.setWindowTitle("Settings dialog")
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()

    '''def print_stats(self):  # nado ubrat' kogda gui budet
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
            print(f"{session_displayname}'s final kills =", session_final_kills)'''

    def check_name(self, ign):
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
        req_wins = req_achievements.get('bedwars_wins')
        req_losses = req_bedwars.get('losses_bedwars')
        if req_wins is None:
            req_wins = 0
        if req_losses is None:
            req_losses = 1
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
                req_beds_broken, req_beds_lost, req_wins, req_losses, 0, 0]

    def get_stats_name(self, name):
        name = name.strip()
        url = f"https://api.hypixel.net/player?key={self.API_key}&name={name}"
        req = requests.get(url).json()
        req_player = req.get('player')
        if req_player is not None:
            return self.get_bw_stats(req_player)

    def get_stats_uuid(self, uuid):
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
        if new_player in self.uuid_dict:
            new_player = self.uuid_dict[new_player]
        new_player = new_player.strip()
        if len(new_player) > 16:  # checking whether it is an ign or a uuid
            new_player_stats = self.get_stats_uuid(new_player)
        else:
            new_player_stats = self.get_stats_name(new_player)
        try:
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

                # overall table updating
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
                    pos, 5, QTableWidgetItem(str(new_player_stats[9])))
                self.overall_stats_table.setItem(
                    pos, 6, QTableWidgetItem(str(new_player_stats[10])))
                self.overall_stats_table.setItem(
                    pos, 7, QTableWidgetItem(str(round(new_player_stats[9] / new_player_stats[10], 3))))
                self.overall_stats_table.setItem(pos, 8, QTableWidgetItem(
                    str(round(new_player_stats[7] / new_player_stats[8], 3))))

                # session table updating
                self.session_stats_table.insertRow(pos)
                self.session_stats_table.setItem(pos, 0, QTableWidgetItem(new_player_stats[0]))
                self.game_stats_table.insertRow(pos)
                self.game_stats_table.setItem(pos, 0, QTableWidgetItem(new_player_stats[0]))

                for i in range(1, 8):
                    self.session_stats_table.setItem(pos, i, QTableWidgetItem("0"))
                for i in range(1, 6):
                    self.game_stats_table.setItem(pos, i, QTableWidgetItem("0"))

                if self.session_is_started:
                    player_join_time = int(time.time())
                    new_player_stats.append(player_join_time)
                    self.stats_before.append([])
                    cur_player, cur_stats = new_player, new_player_stats
                    for i in range(pos, len(self.party_members)):
                        cur_stats, self.stats_before[i] = self.stats_before[i], cur_stats

                self.game_stats.append([])
                cur_player, cur_stats = new_player, new_player_stats
                for i in range(pos, len(self.party_members)):
                    cur_stats, self.game_stats[i] = self.game_stats[i], cur_stats

                print(f'{new_player} was added')
                print(self.party_stats)
                print(self.party_members)
                self.uuid_dict[new_player] = new_player_stats[4]
                print(self.uuid_dict)
        except TypeError:
            print('Request failed, try again later')

    def create_stats_after(self, player_stats):
        i = []
        for i in self.stats_before:
            if i[0] == player_stats[0]:
                break
        stars = player_stats[1] - i[1]
        final_kills = player_stats[2] - i[2]
        final_deaths = player_stats[3] - i[3]
        xp = player_stats[5] - i[5]
        beds_broken = player_stats[7] - i[7]
        beds_lost = player_stats[8] - i[8]
        wins = player_stats[9] - i[9]
        losses = player_stats[10] - i[10]

        return [player_stats[0], stars, final_kills, final_deaths, player_stats[4], xp,
                player_stats[6], beds_broken, beds_lost, wins, losses]

    def remove_player(self, kicked_player):
        ps_index = 'wrong index'
        player_leave_time = int(time.time())
        kicked_player = kicked_player.strip()
        if kicked_player in self.party_members:

            elem = []
            for elem in self.party_stats:
                if elem[0] == kicked_player:
                    ps_index = self.party_stats.index(elem)
                    break
            if self.session_is_started:
                try:
                    kicked_player_stats_after = self.create_stats_after(self.get_stats_uuid(elem[4]))
                    kicked_player_stats_after.append(self.stats_before[ps_index][-1])
                    kicked_player_stats_after.append(player_leave_time)
                    self.stats_after.append(kicked_player_stats_after)
                except TypeError:
                    print('Unable to make a request, try again')

            self.overall_stats_table.removeRow(ps_index)
            self.session_stats_table.removeRow(ps_index)
            del self.party_stats[ps_index]
            for sb in range(0, len(self.stats_before)):
                if self.stats_before[sb][0] == kicked_player:
                    del self.stats_before[sb]
                    break

            print(f"{kicked_player} was removed")
        else:
            print(f'ERROR: {kicked_player} is not in the list')

    def disband_party(self):
        for sa_player in self.party_members:
            if sa_player != self.user_ign:
                self.remove_player(sa_player)
        self.party_members = [self.user_ign]

    def check_client(self):
        if self.bool_debug_is_enabled:
            return "./latest.log"

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
                    if s[0] == 'API_key':
                        self.API_key = s[1].strip()
                        while not apikey:
                            req_link = f'https://api.hypixel.net/player?key={self.API_key}'
                            if requests.get(req_link) == '<Response [403]>':
                                print('Invalid API key, try again')
                                self.API_key = input()
                            else:
                                apikey = True
        if not apikey:
            print('Enter your hypixel API key (you can get it by using /api new on the server)')
            while not api_key_check:
                self.API_key = input()
                req_link = f'https://api.hypixel.net/player?key={self.API_key}&uuid=1eb4482cf46248baba0efa3382da4de2'
                if requests.get(req_link).json().get('player') is None:
                    print('Invalid API key, try again')
                else:
                    with open(self.cfg_file, 'a+') as cfg:
                        cfg.write(f'API_key={self.API_key}' + '\n')
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
                with open(self.cfg_file, 'a+') as cfg:
                    cfg.write(f'Name={ign}={uuid}' + '\n')
                    ign_entered = True

        with open(self.cfg_file) as cfg:
            for cfg_line in cfg:
                s = cfg_line.split('=')
                if s[0] == 'Name':
                    self.add_player(s[2].strip())
                    if self.party_stats == [None]:
                        print(f'ERROR: Unable to get stats of {s[1].strip()}, try restarting the program')
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

    def get_stats_history(self):
        pass

    def start_session(self):
        self.session_start_time = int(time.time())
        for elem in self.party_stats:
            bef = [i for i in elem]
            self.game_stats.append(bef)
            bef.append(self.session_start_time)
            self.stats_before.append(bef)
        self.session_is_started = True
        print('The session was started')
        print(f'Time = {self.session_start_time}')
        print(self.stats_before)

    def end_session(self):
        session_end_time = int(time.time())
        for player in self.party_members:
            self.remove_player(player)
        with open(self.stats_file, 'a+') as ss:
            ss.write(f'SESSION STARTED {self.session_start_time}' + '\n')
        for sa in self.stats_after:
            ign = sa[0]
            final_kills = sa[2]
            final_deaths = sa[3]
            if final_deaths == 0:
                fkdr = final_kills
            else:
                fkdr = round(final_kills / final_deaths, 2)
            level_progress = sa[1]
            xp_progress = sa[5]
            wins = sa[9]
            losses = sa[10]
            join_time = sa[-2]
            leave_time = sa[-1]
            with open(self.stats_file, 'a+') as ss:
                ss.write(f'{ign} {final_kills} {final_deaths} {fkdr} {level_progress} {xp_progress}'
                         f' {wins} {losses} {join_time} {leave_time}' + '\n')
        with open(self.stats_file, 'a+') as ss:
            ss.write('events: ')
        with open(self.stats_file, 'a+') as ss:
            for event in self.events:
                ss.write(f'{event[0]};{event[1]};{event[2]}, ')
            ss.write('\n')
        with open(self.stats_file, 'a+') as ss:
            ss.write(f'SESSION ENDED {session_end_time}' + '\n')
            ss.write('\n')

    def create_event(self, name, event):
        event_time = int(time.time())
        single_event = [name, event, event_time]
        self.events.append(single_event)
        print(single_event)

    def watch_logs(self):
        while not self.session_is_over and self.thread_running:
            if os.stat(self.log_file).st_mtime > self.log_file_last_changed:
                with open(self.log_file) as f:
                    logfile = f.readlines()
                length = len(logfile)

                for line in range(self.logfile_last_line, length):
                    last_line = logfile[line].strip()
                    if last_line[11:31] == '[Client thread/INFO]':
                        self.logfile_last_line = line + 1
                        self.main_cycle(last_line)

                self.log_file_last_changed = os.stat(self.log_file).st_mtime

            else:
                time.sleep(0.5)

    def main_cycle(self, last_line):
        if last_line[-1] == '.' or last_line[-1] == '!':
            last_line = last_line[:-1]
        s = last_line.split()[4:]

        for i in range(len(s)):
            if s[i][0] == '[' and s[i][-1] == ']':
                del s[i]
                break

        if s == ['Protect', 'your', 'bed', 'and', 'destroy', 'the', 'enemy', 'beds']:
            if not self.session_is_started:
                self.start_session()
            self.game_ended_check = False
            self.create_event('event-', 'game_started')
            self.ui_reset_game_stats_table()
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
                    if s[-1] in self.party_members:
                        self.create_event('event-', 'game_won')
                        for pmember in self.party_stats:
                            pmember[9] += 1
                    else:
                        self.create_event('event-', 'game_lost')
                        for pmember in self.party_stats:
                            pmember[10] += 1
                    self.game_ended_check = False
        if len(s) > 1:
            if s[0] == 'Party' and s[1] == 'Members':
                self.party_check = True
        if len(s) == 2:
            if s[0] == 'Bed' and s[1] == 'Wars':
                self.game_ended_check = True
        if len(s) == 4:
            if s[1] == 'joined' and s[3] == 'party':
                self.add_player(s[0])
            if s[0] == 'You' and s[1] == 'left':
                self.disband_party()

        if len(s) == 5:
            if s[2] == 'left' and s[4] == 'party':
                self.remove_player(s[0])
            elif s[0] == 'You' and s[4] == 'party':
                self.disband_party()
                if s[3][-1] == "'":
                    self.add_player(s[3][:-1])
                else:
                    self.add_player(s[3][:-2])
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
            if s[1] == 'has' and s[3] == 'removed':
                self.remove_player(s[0])
            if s[0] == 'You' and s[2] == 'not' and s[6] == 'party':
                self.disband_party()

        if len(s) == 9:
            if s[1] == 'was' and s[2] == 'removed':
                self.remove_player(s[0])

        if len(s) == 14:
            if s[1] == 'party' and s[3] == 'disbanded':
                self.disband_party()

        if len(s) > 0:
            if s[0] == "You'll":
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
                            a = self.party_members.index(player)
                            if player != s[0]:
                                self.party_stats[a][2] += 1
                                self.create_event(f'{player}', 'final_kill')
                            else:
                                self.party_stats[a][3] += 1
                                self.create_event(f'{player}', 'final_death')
                            # self.print_stats()
                if last_line[-18:] == 'fell into the void':
                    player = s[0]
                    if player in self.party_members:
                        for fv_player in self.party_stats:
                            if fv_player[0] == player:
                                fv_player[6] += 1
                                self.create_event(f'{player}', 'voided')
                if len(s) > 1:
                    if s[0] == 'BED' and s[1] == 'DESTRUCTION':
                        player = s[-1]
                        if player in self.party_members:
                            for fv_player in self.party_stats:
                                if fv_player[0] == player:
                                    fv_player[7] += 1
                                    self.create_event(f'{player}', 'bed_broken')
                        if 'Your Bed' in last_line:
                            self.create_event(f'{player}', 'bed_lost')
                            for fv_player in self.party_stats:
                                fv_player[8] += 1
                if len(s) > 3:
                    for player in self.party_members:
                        if 'FINAL' not in s and 'DESTRUCTION' not in s:
                            if player in s:
                                if player == s[-1]:
                                    self.party_stats[self.party_members.index(player)][11] += 1
                                elif s[s.index(player) + 1] == 'was':
                                    self.party_stats[self.party_members.index(player)][12] += 1
            elif self.baldstats_mode == 'api':
                if self.cooldown <= time.time() - 8:
                    self.cooldown = time.time()
                    for i in range(len(self.party_stats)):
                        self.party_stats[i] = self.get_stats_uuid(self.party_stats[i][4])
                        self.ui_make_table()

    def closeEvent(self, event):
        self.thread_running = False
        self.logfile_thread.join()
        self.table_thread.join()
        if self.session_is_started:
            self.end_session()
            self.session_is_over = True
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    frame = Frame()
    # frame.show()  # denchik eto che za shtuka?
    sys.exit(app.exec_())
