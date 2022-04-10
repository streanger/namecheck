import sys
import os
import time
import random
import webbrowser
from tkinter import (
    Tk,
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
    X,
    Y,
)
from pathlib import Path
from termcolor import colored
import namecheck  # my package


class NamecheckGUI(Frame):
    """NamecheckGUI
    title - username; displayed in top label
    data - list of tuples in form -> (key, url, user_exist)
    items_in_row - number of labels in row
    """
    def __init__(self, master, title, data, items_in_row=5):
        super().__init__(master)
        self.title = title
        self.items_in_row = items_in_row
        self.wrapped_data = [data[n:n+self.items_in_row] for n in range(0, len(data), self.items_in_row)]
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master.geometry("{}x{}".format(650, 500))  # width x height
        # self.master.resizable(width=True, height=True)
        self.master.wm_title("namecheck")
        self.pack()
        self.run_gui()
        
    def run_gui(self):
        """create widgets & run gui"""
        # *********** title label ***********
        self.title_label = Label(self.master, text=self.title, fg="black", bg='white', relief="groove")
        self.title_label.pack(expand=NO, fill=BOTH, side=TOP)
        
        # *********** main clickable labels ***********
        self.wrapper_frame = Frame(self.master)
        self.wrapper_frame.pack(expand=YES, fill=BOTH, side=TOP)
        for row_index, row in enumerate(self.wrapped_data):
            row_frame = Frame(self.wrapper_frame)
            row_frame.pack(expand=YES, fill=BOTH, side=TOP)
            for col_index, (key, url, user_exist) in enumerate(row):
                color = self.color_mapping(user_exist)
                # relief arguments: "flat", "raised", "sunken", "ridge", "solid", "groove"
                link_label = Label(row_frame, text=key, fg="blue", bg=color, relief="groove", cursor="hand2")
                link_label.pack(expand=YES, fill=BOTH, side=LEFT)
                """
                bind events: https://python-course.eu/tkinter/events-and-binds-in-tkinter.php
                when using event like <ButtonRelease> or <Button> without specifying button number (1, 2 or 3)
                all of the mouse buttons are binded. To specify use <ButtonRelease-1>, <ButtonRelease-2>, and <ButtonRelease-3>
                
                <Double-Button-1>   -bind double mouse left button
                <ButtonRelease-2>   -bind single mouse middle click & release
                """
                # link_label.bind("<Button-1>", lambda event, url=url: self.click_callback(url))
                link_label.bind("<Double-Button-1>", lambda event, url=url: self.click_callback(url))
                link_label.bind("<ButtonRelease-2>", lambda event, url=url: self.click_callback(url))
                link_label.bind("<Enter>", lambda event, text=url: self.on_start_hover(text))
                link_label.bind("<Leave>", lambda event: self.on_end_hover())
                
        # *********** label with destination url ***********
        self.info_label = Label(self.master, text='', fg="black", bg='white', relief="groove")
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
            color = '#90EE90'  # lightgreen
        elif flag == False:
            color = '#8E9899'  # lightgrey
        elif flag == None:
            color = '#F47B7F'  # lightred
        else:
            color = 'white'
        return color
        
    def on_start_hover(self, text):
        """on mouse start hover cell (label)"""
        self.info_label.config(text=text)
        
    def on_end_hover(self):
        """on mouse end hover cell (label)"""
        self.info_label.config(text='')
        
    def click_callback(self, url):
        """open url in browser"""
        webbrowser.open_new(url)
        
    def on_closing(self):
        """handle application closing"""
        self.master.destroy()
        self.master.quit()
        
        
def example_namecheck_response():
    """for debug"""
    response_values = [('Website{}'.format(x), random.choice(['https://www.google.com', 'https://www.wykop.pl/']), random.choice([True, False, None])) for x in range(28)]
    return response_values
    
    
if __name__ == "__main__":
    # *********** setup ***********
    os.chdir(str(Path(sys.argv[0]).parent))
    os.system('color')
    start_time = time.time()
    
    # *********** username ***********
    args = sys.argv[1:]
    if not args:
        print('[*] usage:')
        print(colored('    python namecheck_gui.py <username>', 'yellow'))
        sys.exit()
    username = args[0]
    print('[*] username: {}'.format(colored(username, 'yellow')))
    
    # *********** collect urls ***********
    namecheck_urls = namecheck.read_json('namecheck_urls.json')
    # namecheck_urls = namecheck.filter_urls(namecheck_urls, ['Slack', 'Spotify'])
    
    # *********** main ***********
    response_values = namecheck.run_main(namecheck_urls, username)
    # response_values = example_namecheck_response()
    print("\n[*] total time: {} [s]".format(round(time.time() - start_time, 4)))
    gui = NamecheckGUI(master=Tk(), title=username, data=response_values)
    gui.mainloop()
    