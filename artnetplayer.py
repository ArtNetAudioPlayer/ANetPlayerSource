import json
import os
import socket

import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from tkinter import *
from tkinter import filedialog

import psutil
import pygame

import artnet_tc
import paths

global framerate
framerate = 30

class ArtNetPlayer(tk.Frame):
    paused = False
    stopped = True

    listofsongs = []
    durationofsongs = []
    songsartnet_time = []

    # Vars for play_update
    fr_prev = 0
    ext_time = 0
    slider_moved = False

    def __init__(self, master, *args, **kwargs):
        # Init Pygame Mixer
        super().__init__(master, **kwargs)
        player = pygame.mixer
        player.init()
        player.music.set_volume(1)
        self.player = player

        self.master = master
        self.master.title('Art-Net Audio Player  v1.0.2')
        self.master.geometry("450x460")
        try:
            wd = sys._MEIPASS
        except AttributeError:
            wd = os.getcwd()
        file_path = os.path.join(wd, 'images/anet.png')
        ico_path = os.path.join(wd, 'images/anet2.ico')
        self.master.iconbitmap(ico_path)
        img = tk.Image("photo", file=file_path)
        # root.tk.call('wm', 'iconphoto', root._w, img)
        self.master.iconphoto(True, img)
        self.master.resizable(False, False)

        global framerate
        # Read JSON config
        try:
            with open('data.json') as json_file:
                data = json.load(json_file)
                for p in data['config']:
                    print('eth_index: ' + str(p['eth_index']))
                    eth_index = int(p['eth_index'])
                    print('fps: ' + p['fps'])
                    framerate = int(p['fps'])
                    print('ip: ' + p['ip'])
                    self.broadcast_ip = p['ip']
                    print('')
        except FileNotFoundError:
            eth_index = 0
            conf_data = {'config': []}
            conf_data['config'].append({
                'eth_index': '0',
                'fps': '30',
                'fps_index': '2',
                'ip': '192.168.1.255'})
            with open('data.json', 'w') as outfile:
                json.dump(conf_data, outfile)

        # Init socket
        self.opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.opened_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, eth_index)
        except OSError:
            print("Wrong eth device!")

        # Define Player Control Button Images
        try:
            wd = sys._MEIPASS
        except AttributeError:
            wd = os.getcwd()
        stop_path = os.path.join(wd, 'images/stop.png')
        pause_path = os.path.join(wd, 'images/pause.png')
        play_path = os.path.join(wd, 'images/play.png')
        self.stop_btn_img = PhotoImage(file=stop_path)
        self.pause_btn_img = PhotoImage(file=pause_path)
        self.play_btn_img = PhotoImage(file=play_path)

        # Create Master Frame
        self.master_frame = Frame(self.master)
        self.master_frame.pack(pady=15)
        # Create Playlist Box
        self.song_box = Listbox(self.master_frame, bg="black", fg="green", width=60, height=7, selectbackground="green",
                                selectforeground="black", relief=FLAT, border=0)
        # Create Music Position Slider
        self.my_slider = ttk.Scale(self.master_frame, from_=0, to=100, orient=HORIZONTAL, value=0,
                                   command=self.slider_update, length=400)
        # Create config window
        self.conf_wind = Toplevel(self.master_frame)    ###
        self.conf_wind.destroy()                        ###

    def create_widgets(self):
        self.song_box.grid(row=0, column=0)
        self.song_box.bind("<<ListboxSelect>>", self.callback_listbox)

        # Create Player Control Frame
        controls_frame = Frame(self.master_frame)
        controls_frame.grid(row=3, column=0, pady=10)

        # Create Player Control Buttons
        play_button = Button(controls_frame, image=self.play_btn_img, borderwidth=0, command=self.play)
        pause_button = Button(controls_frame, image=self.pause_btn_img, borderwidth=0,
                              command=lambda: self.pause(self.paused))
        stop_button = Button(controls_frame, image=self.stop_btn_img, borderwidth=0, command=self.stop)

        play_button.grid(row=0, column=0, padx=10)
        pause_button.grid(row=0, column=1, padx=10)
        stop_button.grid(row=0, column=2, padx=10)

        # Create Music Position Slider
        self.my_slider.grid(row=5, column=0, pady=5)

        # Create ArtNet Frame
        anet_frame = Frame(self.master_frame)
        anet_frame.grid(row=2, column=0, pady=10)

        # Create ArtNet TextBox
        textbox_label = Label(anet_frame, text="ADD TO AUDIO TC", justify=CENTER)
        textbox_label.grid(row=2, column=0, pady=10, padx=5)

        self.anetTextTC = StringVar()
        self.anetTextTC.set('00:00:00:00')
        self.tc_entry = Entry(anet_frame, width=10, textvariable=self.anetTextTC, font=(None, 11), justify=CENTER, relief=FLAT)
        self.tc_entry.grid(row=2, column=1, pady=10, padx=5)

        button = ttk.Button(anet_frame, text="Save", width=8, command=self.save_tc)
        button.grid(row=2, column=2, pady=10, padx=10)

        # Create Labels Frame
        labels_frame = Frame(self.master_frame)
        labels_frame.grid(row=4, column=0, pady=10)

        # Create info Label
        info_labelTC1 = Label(labels_frame, text='AUDIO TC', justify=CENTER)
        info_labelTC1.grid(row=0, column=0, padx=20)

        self.labeltextTC = StringVar()
        self.labeltextTC.set('00:00:00:00')
        info_labelTC1 = Label(labels_frame, textvariable=self.labeltextTC, justify=CENTER, font=(None, 24),
                              foreground="cyan", background="black")
        info_labelTC1.grid(row=1, column=0, padx=20)

        global framerate
        self.labeltextfps = StringVar()
        self.labeltextfps.set('ART-NET TC   '+str(framerate)+' FPS')
        info_labelTC2 = Label(labels_frame, textvariable=self.labeltextfps, justify=CENTER)
        info_labelTC2.grid(row=0, column=2, padx=20)

        self.labeltextATC = StringVar()
        self.labeltextATC.set('00:00:00:00')
        info_labelTC1 = Label(labels_frame, textvariable=self.labeltextATC, justify=CENTER, font=(None, 24),
                              foreground="cyan", background="black")
        info_labelTC1.grid(row=1, column=2, padx=20)

        # Create Status Bar
        self.status_bar = Label(self.master, text='', bd=1, relief=GROOVE, anchor=E,
                                foreground="green", background="black")
        self.status_bar.pack(fill=X, side=BOTTOM, ipady=2)

        # Create Menu
        self.my_menu = Menu(self.master)
        self.master.config(menu=self.my_menu)

        # Create Add Song Menu
        add_rem_menu = Menu(self.my_menu)
        self.my_menu.add_cascade(label="File", menu=add_rem_menu)
        add_rem_menu.add_command(label="Add Audio", command=self.add_songs)
        add_rem_menu.add_command(label="Delete Selected Audio", command=self.delete_song)
        add_rem_menu.add_command(label="Delete All Audios", command=self.delete_all_songs)
        add_rem_menu.add_command(label="Configure", command=self.open_config_window)
        add_ab_menu = Menu(self.my_menu)
        self.my_menu.add_cascade(label="About", menu=add_ab_menu)
        add_ab_menu.add_command(label="About program", command=self.about_window)

    def callback(self, event):
        webbrowser.open_new(event.widget.cget("text"))

    def about_window(self):
        about_wind = Toplevel(self.master_frame)
        about_wind.title("About program")
        x = self.master.winfo_x()
        y = self.master.winfo_y()
        about_wind.geometry("330x160")
        about_wind.geometry("+%d+%d" % (x + 452, y))
        about_wind.resizable(False, False)
        label_conf = tk.Label(about_wind, text="Art-Net Audio Player v1.0.2", font=(None, 14))
        label_conf.grid(row=1, column=0, padx=10, pady=5)
        label_conf = tk.Label(about_wind, text='For any questions write to: pervushkinp@gmail.com')
        label_conf.grid(row=2, column=0, padx=10, pady=5)
        label_conf = tk.Label(about_wind, text='If you like program, please donate')
        label_conf.grid(row=3, column=0, padx=10, pady=5)
        lbl = tk.Label(about_wind, text=r"https://artnetaudioplayer.github.io/", fg="blue", cursor="hand2", font=(None, 14))
        lbl.grid(row=4, column=0, padx=10, pady=5)
        lbl.bind("<Button-1>", self.callback)

    def open_config_window(self):
        self.conf_wind = Toplevel(self.master_frame)      ###
        self.conf_wind.title("Configure params")
        # sets the geometry of toplevel
        x = self.master.winfo_x()
        y = self.master.winfo_y()
        self.conf_wind.geometry("360x220")
        self.conf_wind.geometry("+%d+%d" % (x + 452, y))
        self.conf_wind.resizable(False, False)

        with open('data.json') as json_file:
            data = json.load(json_file)
            for p in data['config']:
                print('eth_index: ' + str(p['eth_index']))
                eth_index = int(p['eth_index'])
                print('fps: ' + p['fps'])
                fps_index = int(p['fps_index'])
                print('ip: ' + p['ip'])
                ip = p['ip']
                print('')

        label_conf = tk.Label(self.conf_wind, text='Art-Net device', justify=RIGHT)
        label_conf.grid(row=0, column=0, padx=10, pady=10)
        self.eth_combobox = ttk.Combobox(self.conf_wind, width=25)
        eth_vars = psutil.net_if_addrs()
        ethlist = []
        for e in eth_vars:
            ethlist.append(e)
        self.eth_combobox['values'] = ethlist
        self.eth_combobox.grid(row=0, column=1, padx=0, pady=10)
        self.eth_combobox.current(eth_index)

        label_conf = tk.Label(self.conf_wind, text='Framerate', justify=RIGHT)
        label_conf.grid(row=1, column=0, padx=10, pady=10)
        self.fps_combobox = ttk.Combobox(self.conf_wind, width=25)
        fps_list = ['24', '25', '30']
        self.fps_combobox['values'] = fps_list
        self.fps_combobox.grid(row=1, column=1, padx=0, pady=10)
        self.fps_combobox.current(fps_index)

        label_conf = tk.Label(self.conf_wind, text='Broadcast IP', justify=RIGHT)
        label_conf.grid(row=2, column=0, padx=10, pady=10)
        self.ip_text = StringVar()
        self.ip_text.set(ip)
        self.ip_entry = Entry(self.conf_wind, width=28, textvariable=self.ip_text)
        self.ip_entry.grid(row=2, column=1, pady=10, padx=5)

        label_conf = tk.Label(self.conf_wind, text='Art-Net packet sending', justify=RIGHT)
        label_conf.grid(row=3, column=0, padx=10, pady=10)
        button2 = ttk.Button(self.conf_wind, text="Check", width=28, command=self.check_udp_send)
        button2.grid(row=3, column=1, pady=10, padx=10)

        self.labeltext_udpcheck = StringVar()
        self.labeltext_udpcheck.set('CHECK: --')
        info_udpcheck = Label(self.conf_wind, textvariable=self.labeltext_udpcheck, justify=CENTER)
        info_udpcheck.grid(row=5, column=0, padx=10, ipadx=28)

        button = ttk.Button(self.conf_wind, text="Save", width=28, command=self.save_config)
        button.grid(row=5, column=1, pady=10, padx=10)

    # Check that selected device answers
    def check_udp_send(self):
        eth_index = self.eth_combobox.current()
        # Close socket
        self.opened_socket.shutdown(socket.SHUT_RDWR)
        self.opened_socket.close()
        # Init socket
        self.opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.opened_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, eth_index)

        self.broadcast_ip = self.ip_entry.get()
        anet_device = self.eth_combobox.get()
        try:
            testbytes = bytearray('Art-Net', 'utf8')
            self.opened_socket.sendto(testbytes, (self.broadcast_ip, 6454))
            self.labeltext_udpcheck.set('CHECK: OK')
        except OSError:
            print("Socket error")
            self.labeltext_udpcheck.set('CHECK: ERR')
            tk.messagebox.showerror(title='Socket Error', message='Fail sending Art-Net packet to ' + anet_device)

    def save_config(self):
        if not self.player.music.get_busy():
            eth_index = self.eth_combobox.current()
            # Check that selected device answers
            self.check_udp_send()

            fps_index = self.fps_combobox.current()
            fps = self.fps_combobox.get()
            # framerate
            framerate = int(fps)
            # Update current fps from config file
            self.labeltextfps.set('ART-NET TC   ' + str(framerate) + ' FPS')

            conf_data = {'config': []}
            conf_data['config'].append({
                'eth_index': eth_index,
                'fps': fps,
                'fps_index': fps_index,
                'ip': self.broadcast_ip})
            with open('data.json', 'w') as outfile:
                json.dump(conf_data, outfile)
            self.labeltext_udpcheck.set('SAVED!')
        else:
            print("Press stop to configure!")

    # show info of selected song
    def active_song_param(self):
        song_path = ""
        song_length = 0
        song_artnet_time = 0
        song_extetion = ""
        song_index = self.song_box.curselection()
        try:
            if song_index[0] >= 0:
                song_index = int(song_index[0])
                song_path = self.listofsongs[song_index]
                song_length = self.durationofsongs[song_index]
                song_artnet_time = self.songsartnet_time[song_index]
                song_extetion = str(song_path[-3:])
                song_extetion = song_extetion.upper()  # make extension uppercase
        except IndexError:
            print("IndexError")
            self.status_bar.config(text=f'NOTHING SELECTED!  ')
            self.my_slider.config(value=0)
            return
        except TypeError:
            print("TypeError")
            self.status_bar.config(text=f'NOTHING SELECTED!  ')
            self.my_slider.config(value=0)
        return [song_path, song_length, song_artnet_time, song_extetion]

    def callback_listbox(self, event):
        #self.stop()
        param_list = self.active_song_param()
        try:
            song_ext = param_list[3]
            song_anet_time = param_list[2]
            #song_index = self.song_box.curselection()
            self.labeltextATC.set(artnet_tc.millis_to_tc(song_anet_time), framerate)
            if song_ext == "WAV":
                self.my_slider.state(['disabled'])
                self.paused = False
            else:
                self.my_slider.state(['!disabled'])
                self.paused = False
        except TypeError:
            print("TypeError callback_listbox")
        self.status_bar.config(text=f'STOPPED  ')

    def play_update(self):
        global framerate

        if not self.player.music.get_busy():
            return
        millis = int(self.player.music.get_pos())

        if self.slider_moved:
            slider_pos = int(self.my_slider.get()) * 1000
            self.ext_time = millis + slider_pos
            self.slider_moved = False

        fr_cur = int((millis / 1000*framerate) % framerate)
        if fr_cur != self.fr_prev:
            param_list = self.active_song_param()
            song_anet_time = param_list[2]
            anet_millis = self.ext_time + millis + song_anet_time
            a1 = artnet_tc.anet_conv(anet_millis, framerate)
            self.opened_socket.sendto(a1, (self.broadcast_ip, 6454))
            self.fr_prev = fr_cur
            # Display current TC
            tc_str = artnet_tc.millis_to_tc(self.ext_time + millis, framerate)
            self.labeltextTC.set(tc_str)
            anet_tc_str = artnet_tc.millis_to_tc(anet_millis, framerate)
            self.labeltextATC.set(anet_tc_str)

        self.my_slider.after(5, self.play_update)

    def track_play(self):
        if self.stopped or self.paused:
            return
        # Get song length of the selected file
        param_list = self.active_song_param()
        song_length = param_list[1]
        # Grab Current Song Elapsed Time
        current_time = pygame.mixer.music.get_pos() / 1000

        if int(self.my_slider.get()) == int(current_time):
            # Update Slider To position
            slider_position = int(song_length)
            self.my_slider.config(to=slider_position, value=int(current_time))
        else:
            # Update Slider To position
            slider_position = int(song_length)
            self.my_slider.config(to=slider_position, value=int(self.my_slider.get()))

            # Move this thing along by one second
            next_time = int(self.my_slider.get()) + 1
            self.my_slider.config(value=next_time)
        # update time
        self.status_bar.after(1000, self.track_play)
        # Increase current time by 1 second
        current_time += 1
        # Output message on the end of audio
        if not self.player.music.get_busy():
            self.stop()

    def play(self):
        try:
            print(self.active_song_param())
            self.stopped = False
            self.song_box.configure(state=DISABLED)
            param_list = self.active_song_param()
            song_ext = param_list[3]
            song_path = param_list[0]
            print(song_ext)
            # Check if play button already pressed
            if self.player.music.get_busy():
                return
            # Pause method behavior due to file extension
            if self.paused:
                # Unpause
                if song_ext == "WAV":
                    self.player.music.unpause()
                    self.paused = False
                    self.status_bar.config(text=f'PLAYING...  ')
                elif song_ext == "MP3" or song_ext == "OGG":
                    self.player.music.play(loops=0, start=int(self.my_slider.get()))
                    self.slider_moved = True
                    self.paused = False
                    self.status_bar.config(text=f'PLAYING...  ')
                else:
                    self.status_bar.config(text=f'WRONG FILE EXTENSION!  ')
                    return
            else:
                self.player.music.load(song_path)
                self.player.music.play(loops=0, start=int(self.my_slider.get()))
                self.status_bar.config(text=f'PLAYING...  ')

                self.tc_entry.config(state='disabled')
                self.my_menu.entryconfig("File", state="disabled")
                # Close config window, if exists
                self.conf_wind.destroy()
            # update every 1 sec
            self.track_play()
            # update every 5 ms
            self.play_update()
        except IndexError:
            print("IndexError play")
            self.enable_gui()
        except TypeError:
            print("TypeError play")
            self.enable_gui()

    # Activate disabled gui items
    def enable_gui(self):
        self.tc_entry.config(state='normal')
        self.my_menu.entryconfig("File", state="normal")
        self.song_box.configure(state=NORMAL)

    def stop(self):
        self.player.music.stop()
        self.enable_gui()
        # song_box.selection_clear(ACTIVE)
        self.stopped = True

        param_list = self.active_song_param()
        song_length = param_list[1]
        song_anet_time = param_list[2]

        slider_position = int(song_length)
        self.my_slider.config(to=slider_position, value=0)
        self.status_bar.config(text=f'STOPPED  ')

        # update Audio TC and ArtNet TC label data
        tc_str = artnet_tc.millis_to_tc(int(self.my_slider.get() * 1000), framerate)
        self.labeltextTC.set(tc_str)
        anet_tc_str = artnet_tc.millis_to_tc(int(self.my_slider.get() * 1000) + song_anet_time, framerate)
        self.labeltextATC.set(anet_tc_str)
        self.slider_moved = True

    def pause(self, is_paused):
        self.paused = is_paused
        if self.paused:
            # Already pressed
            return
        else:
            # Pause
            self.player.music.pause()
            self.paused = True
            self.status_bar.config(text=f'PAUSED  ')

    def save_tc(self):
        song_index = self.song_box.curselection()
        try:
            if song_index[0] >= 0:
                song_index = int(song_index[0])
                print(song_index)
                print(self.listofsongs[song_index])
                tcstr_append = self.anetTextTC.get()
                tclist = tcstr_append.split(':')
                fr_ms = int(round(int(tclist[3]) * 1000 / framerate))
                msecs = int(tclist[0]) * 60 * 60 * 1000 + int(tclist[1]) * 60 * 1000 + int(tclist[2]) * 1000 + fr_ms + 1
                self.songsartnet_time[song_index] = msecs
        except IndexError:
            print("IndexError")
            self.status_bar.config(text=f'SELECT AUDIO TO SAVE TC!  ')
        except TypeError:
            print("TypeError")

    def add_songs(self):
        songs = filedialog.askopenfilenames(initialdir='audio/', title="Choose an Audio File",
                                            filetypes=(("Audio Files", "*.mp3 *.ogg *.wav"),
                                                       ("mp3, ogg Files", "*.mp3 *.ogg"),
                                                       ("wav Files", "*.wav"), ("All Files", "*.*"),))
        # Loop through song list and replace directory info
        for song in songs:
            # Insert into playlist
            song_name = paths.path_leaf(song)
            self.song_box.insert(END, song_name)
            self.listofsongs.append(song)
            song1 = pygame.mixer.Sound(song)
            self.durationofsongs.append(song1.get_length())
            self.songsartnet_time.append(0)
            print(song1.get_length())
            song_length_str = song_name + ' LENGTH: ' + str(int(song1.get_length())) + ' secs  '
            self.status_bar.config(text=song_length_str)
        # set slider to zero pos
        self.my_slider.config(value=0)

    def delete_song(self):
        self.stop()
        # Delete Currently Selected Song
        self.song_box.delete(ANCHOR)
        # Stop Music if it's playing
        self.player.music.stop()

    def delete_all_songs(self):
        self.stop()
        # Delete All Songs
        self.song_box.delete(0, END)
        # Stop Music if it's playing
        self.player.music.stop()

    def slider_update(self, value):
        param_list = self.active_song_param()
        song_path = param_list[0]
        song_length = param_list[1]
        song_anet_time = param_list[2]
        self.player.music.load(song_path)
        slider_size = int(song_length)
        self.my_slider.config(to=slider_size, value=self.my_slider.get())

        # update Audio TC and ArtNet TC label data
        tc_str = artnet_tc.millis_to_tc(int(self.my_slider.get() * 1000), framerate)
        self.labeltextTC.set(tc_str)
        anet_tc_str = artnet_tc.millis_to_tc(int(self.my_slider.get() * 1000) + song_anet_time, framerate)
        self.labeltextATC.set(anet_tc_str)
        self.slider_moved = True

        if self.stopped or self.paused:
            return
        elif not self.stopped or not self.paused:
            pygame.mixer.music.play(loops=0, start=int(self.my_slider.get()))