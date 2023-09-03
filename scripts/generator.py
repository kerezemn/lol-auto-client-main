import os
import time
import json
import sys
import pyautogui
import pyperclip

from .detector import Detector

BASE_CONFIG = {
    "accept_game": False,
    "write_chat": {'write': '', 'times': 0},
    "pick_champ": [],
    "pick_runes": False
}

class Generator:
    def __init__(self) -> None:
        self.is_user_have_config = False
        self.detectors = []
        self.selected_champ = 0

        self.search_queue = [
            ["pick_1", "pick_2", "pick_3"], "chat", "rune_icon", "rune_select", "ready", "wait"
        ]

        # Queue index değişkenleri (okunabilirliği arttirmak için)
        self.PICK_INDEX = 0
        self.CHAT_INDEX = 1
        self.RUNE_ICON_INDEX = 2
        self.RUNE_SELECT_INDEX = 3
        self.READY_INDEX = 4
        self.WAIT_INDEX = 5

        if 'config.json' in os.listdir('.'):
            self.is_user_have_config = True
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        
        else:
            self.config = BASE_CONFIG.copy()

        self.get_input()
    
    def create_config(self) -> None:
        print('Creating new config.')

        for setting in self.config:
            setting_on = input(setting + "(y/n): ") == "y"

            if setting == "pick_champ":
                if setting_on:
                    for i in range(3):
                        char_name = input("Champ %d: " % (i+1))
                        self.config["pick_champ"].append(char_name)
            
            elif setting == "write_chat":
                if setting_on:
                    self.config['write_chat']['write'] = input("What to write: ")
                    self.config['write_chat']['times'] = int(input("How many times: "))
            
            else:
                self.config[setting] = setting_on

        with open('config.json', 'w') as f:
            json.dump(self.config, f)
        
        print('Config is created.')
    
    def delay(self, delay_seconds : float) -> None:
        """ Ana delayi saglar. """
        start = time.time()
        while time.time() - start < delay_seconds:
            pass
    
    def get_input(self):
        if self.is_user_have_config:
            if input('Are you want to continue with your last config? (y/n): ') != 'y':
                self.config = BASE_CONFIG.copy()
                self.create_config()
        else:
            self.create_config()
    
    def game_accepted(self) -> None:
        """ Hazirlik lobisi degiskenlerini resetler. """
        self.current_queue = self.search_queue.copy()  
    
    def get_searching(self) -> str:
        current = self.current_queue[0]
        if type(current) is str:
            return current
        return current[0] # Current 'str' değil ise kesinlikle 'list[str]' dir.

    def lock_detected(self) -> None:
        pick_array = self.current_queue[0]
        if len(pick_array) > 1:
            pick_array.pop(0)
        else: # Detectleyecek champ kalmadiginda
            # TODO: Ready, rün gibi champ ile baglantili şeyleri de kuyruktan kaldir.
            self.current_queue.pop(0)
    
    def champ_selected(self) -> None:
        """ Champe tiklandiginda triggerlanir. """
        self.selected_champ = 4 - len(self.current_queue[0])
        self.current_queue.pop(0)
    
    def champ_locked(self) -> None:
        """ Ready basildiginda triggerlanir. """
        self.current_queue.pop(0)
    
    def chat_clicked(self) -> None:
        """ Chate tiklandiginda triggerlanir. """

        pyperclip.copy(self.config['write_chat']['write'])

        for _ in range(self.config['write_chat']['times']):
            pyautogui.hotkey("ctrl", "v")
            pyautogui.press('enter')
        
        self.current_queue.pop(0)

    def rune_icon_clicked(self) -> None:
        """ Rün butonuna basildiginda triggerlanir. """
        self.rune_select_detector.change_image(0, "./general/rune_%d.png" % self.selected_champ)
        self.current_queue.pop(0)

    def rune_selected(self) -> None:
        """ Rün seçildiğinde triggerlanir. """
        self.current_queue.pop(0)

    def close(self) -> None:
        """ Programi kapatir chate '/close' yazildiginda veya programdan cikildiginda triggerlanir. """
        sys.exit()
    
    def generate_detectors(self):
        """ Confige göre kuyruğu düzenler ve detectorleri oluşturur. """

        # Config'e göre kuyruk düzenlenir.
        if not(self.config['write_chat']['times']) or not(self.config['write_chat']['write']):
            self.search_queue.pop(self.CHAT_INDEX)
        
        if not(self.config['pick_champ']):
            self.search_queue.pop(self.PICK_INDEX)
        
        elif len(self.config['pick_champ']) != 3:
            for _ in range(3 - len(self.config['pick_champ'])):
                self.search_queue[self.PICK_INDEX].pop()
        
        self.current_queue = self.search_queue.copy()

        # Confige göre detectorleri oluşturur.
        if self.config['accept_game']:
            self.detectors.append(Detector("./general/accept.png", 1, 0.95, True, self.game_accepted, alternative_paths = ["./general/interactive_accept.png"]))
        
        if self.config['pick_champ']:
            self.detectors.append(
                Detector("./general/ready.png", 1, 0.90, True, self.champ_locked, self.get_searching, "ready")
            )

            for i, champ in enumerate(self.config['pick_champ']):
                self.detectors.append(
                    Detector("./picks/%s.png" % champ, 0.5, 0, True, self.champ_selected, self.get_searching, "pick_%d" % (i+1))
                )

                self.detectors.append(
                    Detector("./locked_picks/%s.png" % champ, 0.5, 0, False, self.lock_detected, self.get_searching, "pick_%d" % (i+1))
                )
        
        if self.config['write_chat']['times'] and self.config['write_chat']['write']:
            self.detectors.append(
                Detector("./general/chat.png", 0.5, 0.95, True, self.chat_clicked, self.get_searching, "chat")
            )
        
        if self.config['pick_runes']:
            self.detectors.append(
                Detector("./general/rune_icon.png", 0.5, 0.95, True, self.rune_icon_clicked, self.get_searching, "rune_icon")
            )

            self.rune_select_detector = Detector(
                "./general/rune_1.png", 0.5, 0, True, self.rune_selected, self.get_searching, "rune_select"
            )

            self.detectors.append(self.rune_select_detector)
        
        self.detectors.append(Detector("./general/close.png", 0.5, 0.95, trigger_func = self.close))

    def run(self) -> None:
        self.generate_detectors()
        
        # Configi kullaniciya printler.
        print("Started with this config:")
        print("{")
        for setting, value in self.config.items():
            print("   " + setting + " : " + str(value))
        print("}")

        # Main Loop
        while True:
            try:
                for detector in self.detectors:
                    detector.update()

                self.delay(0.1)
            
            except KeyboardInterrupt: # Ctrl + C
                self.close()