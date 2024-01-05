# GUI
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
from PIL import ImageTk

# functionality
import json
import keyboard, mouse
import time
import pathlib, os

# local
import files

class App():
    def __init__(self):
        # read config
        self.config_file = os.path.join(pathlib.Path(__file__).parent.resolve(), "config.json") # joins arg 0 and the desired filename, which is better than relative paths
        try:
            self.config = files.read_config_file(self.config_file)
        except FileNotFoundError:
            self.config = {}
        self.macro_events = []
        self.kb_hook = None
        self.mouse_hook = None
        self.recording = False
        self.playback_paused = True

        # initialize dict to store data across multiple button presses on play/pause
        self.playback_metadata = {
            "offset": 0,
            "index": 0
        }

        # create main window format -- change it to make it look better, just proto-typey atm
        self.root = tk.Tk()
        self.root.title("MacroFlow Recorder")

        # load assets
        self.btn_play_img = ImageTk.PhotoImage(file="assets/play-button-icon.png")
        self.btn_rec_img = ImageTk.PhotoImage(file="assets/circle-icon.png")
        self.btn_pause_img = ImageTk.PhotoImage(file="assets/pause-button-icon.png")
        self.btn_save_img = ImageTk.PhotoImage(file="assets/save-icon.png")

        # variable to keep track of row variable - makes it easier to add more elements inbetween existing elements later on
        row = 0

        # create labels & buttons
        self.lbl_top = ttk.Label(self.root, text="Record and Playback your Keyboard and Mouse Inputs!")
        self.lbl_top.grid(row=row, columnspan=3)
        
        row += 1


        self.btn_play = ttk.Button(self.root, width=150, text='Play', command=(lambda: self.btn_play_hook()), image=self.btn_play_img)
        self.btn_play.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)

        self.btn_save = ttk.Button(self.root, width=150, text="Save", command=(lambda: self.btn_save_hook()), image=self.btn_save_img)
        self.btn_save.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)

        self.btn_rec = ttk.Button(self.root, width=150, text='Record', command=(lambda: self.btn_rec_hook()), image=self.btn_rec_img)
        self.btn_rec.grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)

        row += 1


        # create entries for recording/stopping/... hotkeys
        if "htk_btn_play_combo" in self.config:
            self.htk_btn_play_combo = self.config["htk_btn_play_combo"]
        else:
            self.htk_btn_play_combo = "ctrl+shift+f11"
        
        if "htk_btn_rec_combo" in self.config:
            self.htk_btn_rec_combo = self.config["htk_btn_rec_combo"]
        else:
            self.htk_btn_rec_combo = "ctrl+shift+f12"

        self.htk_btn_play = keyboard.add_hotkey(self.htk_btn_play_combo, self.btn_play_hook)
        self.htk_btn_rec = keyboard.add_hotkey(self.htk_btn_rec_combo, self.btn_rec_hook)

        self.btn_htk_btn_play = ttk.Button(self.root, text=self.htk_btn_play_combo, command=(lambda: self.hotkey_record_hook("play")))
        self.btn_htk_btn_play.grid(row=row, column=0, padx=5)

        self.btn_htk_btn_rec = ttk.Button(self.root, text=self.htk_btn_rec_combo, command=(lambda: self.hotkey_record_hook("rec")))
        self.btn_htk_btn_rec.grid(row=row, column=2, padx=5)

        row += 1


        # add checkbox to toggle playback loop
        self.var_loop = tk.IntVar()
        self.chk_loop = ttk.Checkbutton(self.root, text="Loop Playback", variable=self.var_loop, onvalue=1, offvalue=0)
        self.chk_loop.grid(row=row, padx=5)

        row += 1


        # create separator to visually seperate the entries for the hotkeys and the entry for the file path
        self.sep_file = ttk.Separator(self.root, orient="horizontal")
        self.sep_file.grid(row=row, column=0, sticky=tk.EW, columnspan=3, padx=5, pady=5)

        row += 1


        self.sty_root = ttk.Style(self.root)
        self.sty_root.configure("TSeparator", background="gray")

        # create entries and buttons to load recordings
        self.lbl_file = ttk.Label(self.root, text="Load Macro from previously saved recording:")
        self.lbl_file.grid(row=row, columnspan=3, sticky=tk.W, padx=5)

        row += 1


        self.ent_file = ttk.Entry(self.root, width=45)
        self.ent_file.bind("<Return>", (lambda _: self.btn_load_hook(self.ent_file.get())))
        self.ent_file.grid(row=row, columnspan=2, sticky=tk.W, padx=5, pady=5)

        self.btn_load = ttk.Button(self.root, width=9, text="Load", command=(lambda: self.btn_load_hook(self.ent_file.get())))
        self.btn_load.grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)

        self.btn_browse = ttk.Button(self.root, width=9, text="Browse", command=(lambda: self.btn_browse_hook()))
        self.btn_browse.grid(row=row, column=2, sticky=tk.E, padx=5, pady=5)

        row += 1


        # create separator to visually seperate the entry for the file path and the autoclicker
        self.sep_file = ttk.Separator(self.root, orient="horizontal")
        self.sep_file.grid(row=row, column=0, sticky=tk.EW, columnspan=3, padx=5, pady=5)

        row += 1


        self.sty_root = ttk.Style(self.root)
        self.sty_root.configure("TSeparator", background="gray")

        # create ui elements for the autoclicker
        if "autoclicker_key" in self.config:
            self.autoclicker_key = self.config["autoclicker_key"]
        else:
            self.autoclicker_key = "left"

        if "htk_autoclicker" in self.config:
            self.htk_autoclicker_combo = self.config["htk_autoclicker"]
        else:
            self.htk_autoclicker_combo = "ctrl+shift+f1"

        if "autoclicker_speed" in self.config:
            self.autoclicker_speed = self.config["autoclicker_speed"]
        else:
            self.autoclicker_speed = 10

        self.autoclicker_active = False

        self.lbl_autoclicker = ttk.Label(self.root, text="Autoclicker")
        self.lbl_autoclicker.grid(row=row, sticky=tk.W, padx=5)

        self.lbl_autoclicker_key_select = ttk.Label(self.root, text="Select Button:")
        self.lbl_autoclicker_key_select.grid(row=row, column=1, padx=5)

        self.btn_autoclicker_start = ttk.Button(self.root, text="Start", command=(lambda: self.autoclicker_hook()))
        self.btn_autoclicker_start.grid(row=row, column=2, padx=5, pady=5)

        row += 1


        self.lbl_autoclicker_speed = ttk.Label(self.root, text="Click speed:")
        self.lbl_autoclicker_speed.grid(row=row, sticky=tk.W, padx=5, pady=5)

        self.ent_autoclicker_speed = ttk.Entry(self.root, width=9)
        self.ent_autoclicker_speed.insert(0, str(self.autoclicker_speed))
        self.ent_autoclicker_speed.bind("<Return>", (lambda _: self.autoclicker_speed_hook(self.ent_autoclicker_speed.get())))
        self.ent_autoclicker_speed.grid(row=row,  sticky=tk.E, padx=5, pady=5)

        self.btn_autoclicker_key_select = ttk.Button(self.root, text=self.autoclicker_key, command=(lambda: self.autoclicker_key_hook()))
        self.btn_autoclicker_key_select.grid(row=row, column=1, padx=5, pady=5)

        self.btn_htk_autoclicker = ttk.Button(self.root, text=self.htk_autoclicker_combo, command=(lambda: self.hotkey_record_hook("autoclicker")))
        self.btn_htk_autoclicker.grid(row=row, column=2, padx=5)

        row += 1


        self.htk_autoclicker = keyboard.add_hotkey(self.htk_autoclicker_combo, self.autoclicker_hook)

        self.run()
    
    def kb_callback(self, event):
        json_event = json.loads(event.to_json())
        json_event['type'] = "kb"
        self.macro_events.append(json_event)
    
    def mouse_callback(self, event):
        json_event = {}
        if type(event) == mouse._mouse_event.MoveEvent:
            json_event['type'] = "move"
            json_event['x'] = event.x
            json_event['y'] = event.y
            json_event['time'] = event.time
        elif type(event) == mouse._mouse_event.ButtonEvent:
            json_event['type'] = "click"
            json_event['event_type'] = event.event_type
            json_event['button'] = event.button
            json_event['time'] = event.time
        elif type(event) == mouse._mouse_event.WheelEvent:
            json_event['type'] = "wheel"
            json_event['delta'] = event.delta
            json_event['time'] = event.time
        self.macro_events.append(json_event)

    def btn_rec_hook(self):
        if not self.recording:
            self.macro_events = []
        if not self.kb_hook:
            self.kb_hook = keyboard.hook(self.kb_callback)
            self.mouse_hook = mouse.hook(self.mouse_callback)
            self.btn_rec.configure(image=self.btn_pause_img)
        else:
            keyboard.unhook(self.kb_hook)
            mouse.unhook(self.mouse_hook)
            self.kb_hook = None
            self.mouse_hook = None
            self.btn_rec.configure(image=self.btn_rec_img)
        # toggle recording state
        self.recording = not self.recording

    # this function only toggles the playback state and keeps track of the additional time offset, the actual playback is done by playback_listener
    def btn_play_hook(self):
        if self.macro_events == []:
             return
        else:
            self.playback_paused = not self.playback_paused

        if self.playback_paused:
            self.btn_play.configure(image=self.btn_play_img)
        else:
            self.btn_play.configure(image=self.btn_pause_img)

        self.playback_metadata["offset"] = 0
            
    def playback_listener(self):
        if not self.playback_paused:
            event = self.macro_events[self.playback_metadata["index"]]
            if self.playback_metadata["offset"] == 0:
                self.playback_metadata["offset"] = time.time() - event['time']
            
            if event['type'] == "kb":
                while (event['time'] + self.playback_metadata["offset"] > time.time()):
                    time.sleep(0.001)
                if event['event_type'] == "down":
                    keyboard.send(event['scan_code'], True, False)
                else:
                    keyboard.send(event['scan_code'], False, True)
            elif event['type'] == "move":
                while (event['time'] + self.playback_metadata["offset"] > time.time()):
                    time.sleep(0.001)
                mouse.move(event['x'], event['y'])
            elif event['type'] == "click":
                while (event['time'] + self.playback_metadata["offset"] > time.time()):
                    time.sleep(0.001)
                if event['event_type'] == "down":
                    mouse.press(event['button'])
                elif event['event_type'] == "up":
                    mouse.release(event['button'])
            elif event['type'] == "wheel":
                while (event['time'] + self.playback_metadata["offset"] > time.time()):
                    time.sleep(0.001)
                mouse.wheel(event['delta'])

            self.playback_metadata["index"] += 1
            if self.playback_metadata["index"] == len(self.macro_events):
                self.playback_metadata = {
                    "offset": 0,
                    "index": 0
                }
                self.playback_paused = True
                self.btn_play.configure(image=self.btn_play_img)
                if self.var_loop.get():
                    self.btn_play_hook()
        self.root.after(1, self.playback_listener)

    def btn_save_hook(self):
        filename = filedialog.asksaveasfilename(initialdir="/", title="Save as", filetypes = (("MacroFlow Recordings", "*.mfr"),("all files","*.*")))
        if "." not in filename:
            filename += ".mfr"
        if filename != "" and filename != ".mfr":
            files.write_json_file(self.macro_events, filename)


    def do_nothing_hook(self, _):
        pass

    def btn_load_hook(self, input):
        # for some reason only works, if a hook was set up earlier in the program
        # likely the method start_if_necessary of the GenericListener class of the keyboard module
        # preferred way to fix this is to invoke that without unnecessarily setting the hook, although this works, it's kind of messy
        # looked through it though and it doesn't really seem like it "can" or should be invoked from outside it's own module
        self.kb_hook = keyboard.hook(self, self.do_nothing_hook)
        self.kb_hook = None

        try:
            self.macro_events = files.read_macro_file(input)
        except FileNotFoundError:
            messagebox.showerror("File not found!", "Please enter a valid path.")

    def btn_browse_hook(self):
        initialdir = "/"
        if "initialdir" in self.config:
            initialdir = self.config["initialdir"]
        filename = filedialog.askopenfilename(initialdir=initialdir, title="Select file", filetypes = (("MacroFlow Recordings", "*.mfr"),("all files","*.*")))
        self.ent_file.delete(0, tk.END)
        self.ent_file.insert(0, filename)
        self.config["initialdir"] = filename
        files.write_json_file(self.config, self.config_file)

    # messy right now, because literal strings are used in if/else-statements, I know the hotkey itself, can be changed, but idk right now how to change self.htk_btn_*_combo, with it being passed to a function
    # the other option would be dynamic conversion of strings to variable names, but I'd rather avoid that if possible
    def hotkey_record_hook(self, hotkey_type):
        self.hotkey_window = tk.Toplevel(self.root)
        self.hotkey_window.geometry("200x100")
        self.hotkey_window.title("Enter Hotkey")


        if hotkey_type == "play":
            self.lbl_hotkey = ttk.Label(self.hotkey_window, text=self.htk_btn_play_combo)
        elif hotkey_type == "rec":
            self.lbl_hotkey = ttk.Label(self.hotkey_window, text=self.htk_btn_rec_combo)
        elif hotkey_type == "autoclicker":
            self.lbl_hotkey = ttk.Label(self.hotkey_window, text=self.htk_autoclicker_combo)
        self.lbl_hotkey.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        self.hotkey_record_text = ""
        self.keys_down = []

        self.btn_hotkey_ok = ttk.Button(self.hotkey_window, text="OK", command=(lambda: self.save_hotkey(hotkey_type)))
        self.btn_hotkey_ok.place(relx=0.5, rely=0.8, anchor=tk.CENTER)

        self.record_new = True
        self.kb_htk_hook = keyboard.hook(self.hotkey_input_callback)
    
    def save_hotkey(self, hotkey_type):
        if hotkey_type == "play":
            keyboard.remove_hotkey(self.htk_btn_play)
            self.htk_btn_play = keyboard.add_hotkey(self.hotkey_record_text, self.btn_play_hook)
            self.htk_btn_play_combo = self.hotkey_record_text
            self.btn_htk_btn_play.config(text=self.htk_btn_play_combo)
            self.config["htk_btn_play_combo"] = self.htk_btn_play_combo
        elif hotkey_type == "rec":
            keyboard.remove_hotkey(self.htk_btn_rec)
            self.htk_btn_rec = keyboard.add_hotkey(self.hotkey_record_text, self.btn_rec_hook)
            self.htk_btn_rec_combo = self.hotkey_record_text
            self.btn_htk_btn_rec.config(text=self.htk_btn_rec_combo)
            self.config["htk_btn_rec_combo"] = self.htk_btn_rec_combo
        elif hotkey_type == "autoclicker":
            keyboard.remove_hotkey(self.htk_autoclicker)
            self.htk_autoclicker = keyboard.add_hotkey(self.hotkey_record_text, self.btn_autoclicker_start)
            self.htk_autoclicker_combo = self.hotkey_record_text
            self.btn_htk_autoclicker.config(text=self.htk_autoclicker_combo)
            self.config["htk_autoclicker_combo"] = self.htk_autoclicker_combo
        
        files.write_json_file(self.config, self.config_file)
        keyboard.unhook(self.kb_htk_hook)
        self.hotkey_window.destroy()
        self.hotkey_window = None
        self.lbl_hotkey = None
        self.btn_hotkey_ok = None
        self.kb_htk_hook = None
        self.record_new = False
        self.hotkey_record_text = ""
        self.keys_down = []

    def hotkey_input_callback(self, event):
        json_event = json.loads(event.to_json())
        if self.record_new:
            if self.keys_down == []:
                self.hotkey_record_text = ""
            if json_event['event_type'] == "down":
                if json_event['scan_code'] not in self.keys_down:
                    if self.hotkey_record_text == "":
                        self.hotkey_record_text += json_event['name']
                        self.lbl_hotkey.config(text=self.hotkey_record_text)
                    else:
                        self.hotkey_record_text += "+%s"%json_event['name']
                        self.lbl_hotkey.config(text=self.hotkey_record_text)
                    self.keys_down.append(json_event['scan_code'])
            else:
                self.keys_down.remove(json_event['scan_code'])
                self.record_new = False
        else:
            if json_event['event_type'] == "up":
                self.keys_down.remove(json_event['scan_code'])
            if self.keys_down == []:
                self.record_new = True

    def autoclicker_hook(self):
        self.autoclicker_active = not self.autoclicker_active
        if self.autoclicker_active:
            self.btn_autoclicker_start.config(text="Stop")
        else:
            self.btn_autoclicker_start.config(text="Start")
    
    def autoclicker_key_hook(self):
        self.hotkey_window = tk.Toplevel(self.root)
        self.hotkey_window.geometry("200x100")
        self.hotkey_window.title("Choose Mouse Button")

        self.lbl_hotkey = ttk.Label(self.hotkey_window, text=self.autoclicker_key) 
        self.lbl_hotkey.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        self.autoclicker_record_text = ""
        self.autoclicker_inputs = []

        self.btn_hotkey_ok = ttk.Button(self.hotkey_window, text="OK", command=(lambda: self.save_autoclicker_key()))
        self.btn_hotkey_ok.place(relx=0.5, rely=0.8, anchor=tk.CENTER)

        self.record_new = True
        self.mouse_htk_hook = mouse.hook(self.autoclicker_key_input_callback)

    def autoclicker_key_input_callback(self, event):
        if type(event) == mouse._mouse_event.ButtonEvent:
            if event.event_type == "down":
                self.autoclicker_inputs.append(event.button)
                if len(self.autoclicker_inputs) >= 2:
                    self.autoclicker_record_text = self.autoclicker_inputs[-2:-1]
                else:
                    self.autoclicker_record_text = self.autoclicker_inputs[0]
                self.lbl_hotkey.config(text=self.autoclicker_record_text)

    def save_autoclicker_key(self):
        self.autoclicker_key = self.autoclicker_record_text
        self.btn_autoclicker_key_select.config(text=self.autoclicker_record_text)
        self.config["autoclicker_key"] = self.autoclicker_record_text
        files.write_json_file(self.config, self.config_file)
        mouse.unhook(self.mouse_htk_hook)
        self.hotkey_window.destroy()
        self.hotkey_window = None
        self.lbl_hotkey = None
        self.btn_hotkey_ok = None
        self.mouse_htk_hook = None
        self.autoclicker_record_text = ""
        self.autoclicker_inputs = []
    
    def autoclicker_listener(self):
        if self.autoclicker_active:
            mouse.click(self.autoclicker_key)
        self.root.after(int(self.autoclicker_speed), self.autoclicker_listener)

    def autoclicker_speed_hook(self, input):
        try:
            speed = int(input)
            if speed > 0:
                self.autoclicker_speed = speed
                self.config["autoclicker_speed"] = speed
                files.write_json_file(self.config, self.config_file)
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Autoclicker speed!", "Speed must be a positive integer (time between clicks in milliseconds).")        

    def run(self):
        self.root.after(1, self.playback_listener)
        self.root.after(1, self.autoclicker_listener)
        self.root.mainloop()

if __name__ == "__main__":
    App()