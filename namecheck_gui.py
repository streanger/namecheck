import sys
import os
import time
import random
import pyperclip
import webbrowser
import threading
from tkinter import (
    Tk,
    Menu,
    Entry,
    Frame,
    Widget,
    Label,
    Button,
    font,
    YES,
    NO,
    TOP,
    BOTTOM,
    LEFT,
    RIGHT,
    BOTH,
    HORIZONTAL,
    X,
    Y,
)

# from tkinter.ttk import Progressbar  # TODO
from pathlib import Path
from termcolor import colored
import namecheck  # my package


class NamecheckGUI(Frame):
    """NamecheckGUI
    urls - list of urls to be checked
    items_in_row - number of labels in row
    """

    def __init__(self, master, urls, items_in_row=5):
        super().__init__(master)
        self.items_in_row = items_in_row
        self.urls = urls
        self.labels_mapping = {}
        data = list(urls.keys())
        self.wrapped_data = [
            data[n : n + self.items_in_row]
            for n in range(0, len(data), self.items_in_row)
        ]
        self.accounts_found = None
        self.search_thread = None
        self.thread_works = False
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master.geometry("{}x{}".format(650, 500))  # width x height
        # self.master.resizable(width=True, height=True)
        self.master.wm_title("namecheck")
        self.pack()
        self.run_gui()

    def entry_callback(self, event):
        """entry widget event callback"""
        if self.thread_works:
            # print('[*] already works, wait for finish')  # DEBUG
            return None
        self.master.focus()  # unfocus from entry
        self.query = self.username_entry.get().strip()
        if not self.query:
            return None
        # print(colored('[*] query: {}'.format(self.query)))  # DEBUG
        self.clear_labels()
        self.search_thread = threading.Thread(target=self.search_accounts)
        self.search_thread.start()
        self.thread_works = True
        # disable entry before new run
        self.username_entry.config(state="disabled")  # disabled, readonly, normal
        total_threads = threading.enumerate()
        # print('[*] total_threads: {}'.format(total_threads))  # DEBUG
        return None

    def search_accounts(self):
        """search for accounts using asyncio"""
        # print(colored('[*] searching for accounts', 'cyan'))  # DEBUG
        self.accounts_found = namecheck.run_main(self.urls, self.query)
        # print(colored('[*] updating labels', 'cyan'))  # DEBUG
        self.update_labels()
        self.thread_works = False
        self.username_entry.config(state="normal")
        return None

    def clear_labels(self):
        """set white background for each"""
        color = self.color_mapping("")
        for link_label in self.labels_mapping.values():
            link_label.config(bg=color)
        return None

    def update_labels(self):
        for (key, url, value) in self.accounts_found:
            link_label = self.labels_mapping[key]
            color = self.color_mapping(value)
            link_label.config(bg=color)

            # unbind previous events
            link_label.unbind("<Double-Button-1>")
            link_label.unbind("<ButtonRelease-2>")
            link_label.unbind("<Button-3>")
            link_label.unbind("<Enter>")
            link_label.unbind("<Leave>")

            # bind new events
            link_label.bind(
                "<Double-Button-1>", lambda event, url=url: self.click_callback(url)
            )
            link_label.bind(
                "<ButtonRelease-2>", lambda event, url=url: self.click_callback(url)
            )
            link_label.bind("<Button-3>", lambda event, url=url: self.popup(event, url))
            link_label.bind(
                "<Enter>", lambda event, text=url: self.on_start_hover(text)
            )
            link_label.bind("<Leave>", lambda event: self.on_end_hover())

        return None

    def run_gui(self):
        """create widgets & run gui"""
        # *********** title label ***********
        self.username_entry = Entry(
            self.master,
            text="",
            relief="groove",
            justify="center",
        )
        self.username_entry.bind("<Return>", self.entry_callback)
        self.username_entry.pack(expand=NO, fill=BOTH, side=TOP)
        # TODO: progress bar
        # self.prog_bar = Progressbar(self.master, orient=HORIZONTAL, length=100, mode='determinate', value=0)
        # self.prog_bar.pack(expand=NO, fill=BOTH, side=TOP)
        # self.prog_bar['value'] = 40

        # *********** main clickable labels ***********
        self.wrapper_frame = Frame(self.master)
        self.wrapper_frame.pack(expand=YES, fill=BOTH, side=TOP)
        for row_index, row in enumerate(self.wrapped_data):
            row_frame = Frame(self.wrapper_frame)
            row_frame.pack(expand=YES, fill=BOTH, side=TOP)
            for col_index, (key) in enumerate(row):
                url = ""  # at init
                color = self.color_mapping("")  # white
                # relief arguments: "flat", "raised", "sunken", "ridge", "solid", "groove"
                link_label = Label(
                    row_frame,
                    text=key,
                    fg="blue",
                    bg=color,
                    relief="groove",
                    cursor="hand2",
                )
                link_label.pack(expand=YES, fill=BOTH, side=LEFT)
                """
                bind events: https://python-course.eu/tkinter/events-and-binds-in-tkinter.php
                when using event like <ButtonRelease> or <Button> without specifying button number (1, 2 or 3)
                all of the mouse buttons are binded. To specify use <ButtonRelease-1>, <ButtonRelease-2>, and <ButtonRelease-3>
                
                <Double-Button-1>   -bind double mouse left button
                <ButtonRelease-2>   -bind single mouse middle click & release
                """
                link_label.bind(
                    "<Double-Button-1>", lambda event, url=url: self.click_callback(url)
                )
                link_label.bind(
                    "<ButtonRelease-2>", lambda event, url=url: self.click_callback(url)
                )
                link_label.bind(
                    "<Button-3>", lambda event, url=url: self.popup(event, url)
                )
                link_label.bind(
                    "<Enter>", lambda event, text=url: self.on_start_hover(text)
                )
                link_label.bind("<Leave>", lambda event: self.on_end_hover())

                # store reference to all labels
                self.labels_mapping[key] = link_label

        # *********** label with destination url ***********
        self.info_label = Label(
            self.master, text="", fg="black", bg="white", relief="groove"
        )
        self.info_label.pack(expand=NO, fill=BOTH, side=TOP)

        # *********** lift, get focus ***********
        self.master.update()
        self.master.attributes("-topmost", True)
        self.master.lift()  # move window to the top
        self.master.focus_force()
        return None

    def color_mapping(self, flag):
        """labels color mapping
            lightgreen: #90EE90
            lightgrey:  #8E9899
            lightred:   #F47B7F
        https://www.color-name.com/neutral-cyan.color
        """
        if flag == True:
            color = "#90EE90"  # lightgreen
        elif flag == False:
            color = "#8E9899"  # lightgrey
        elif flag == None:
            color = "#F47B7F"  # lightred
        else:
            color = "white"
        return color

    def popup(self, event, url):
        """popup window for handling mouse rightclick
        https://stackoverflow.com/questions/12014210/tkinter-app-adding-a-right-click-context-menu
        https://www.askpython.com/python-modules/tkinter/menu-bar-and-menubutton
        """
        popup_menu = Menu(self, tearoff=0)
        popup_menu.add_command(label="copy", command=lambda: pyperclip.copy(url))
        try:
            popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            popup_menu.grab_release()
        return None

    def on_start_hover(self, text):
        """on mouse start hover cell (label)"""
        self.info_label.config(text=text)

    def on_end_hover(self):
        """on mouse end hover cell (label)"""
        self.info_label.config(text="")

    def click_callback(self, url):
        """open url in browser"""
        webbrowser.open_new(url)

    def on_closing(self):
        """handle application closing"""
        self.master.destroy()
        self.master.quit()


def fake_namecheck_response():
    """for debug purposes"""
    response_values = [
        (
            "Website{}".format(x),
            random.choice(["https://www.google.com", "https://www.wykop.pl/"]),
            random.choice([True, False, None]),
        )
        for x in range(28)
    ]
    response_values = [
        (
            "ab" * random.randrange(1, 5),
            "http://fake-{}-url.com".format(x),
            random.choice((True, False)),
        )
        for x in range(87)
    ]
    urls = [url for url, _, _ in response_values]
    return response_values


if __name__ == "__main__":
    # *********** setup ***********
    if os.name == "nt":
        os.system("color")

    # *********** collect urls ***********
    namecheck_urls = namecheck.read_json("namecheck_urls.json")
    # namecheck_urls = namecheck.filter_urls(namecheck_urls, ['Slack', 'Spotify'])

    # *********** main ***********
    gui = NamecheckGUI(master=Tk(), urls=namecheck_urls)
    gui.mainloop()

"""
todo:
    -issue with: Can not load response cookies: Illegal key 'httponly,msToken'
    https://stackoverflow.com/questions/47895765/use-asyncio-and-tkinter-or-another-gui-lib-together-without-freezing-the-gui

"""
