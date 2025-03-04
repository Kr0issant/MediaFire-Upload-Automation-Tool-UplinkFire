import time, json, pyperclip, os, secrets, random, platform
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from tkinter import scrolledtext
from pathlib import Path
from mailtm import Email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

accounts_path = Path(__file__).resolve().parent / 'accounts.json'
settings_path = Path(__file__).resolve().parent / 'settings.json'

# Load settings from file
with open(settings_path, 'r') as F:
    settings = json.load(F)
    wait_duration = settings['wait_duration']  # Timeout duration for actions
    upload_duration = settings['upload_duration']  # Timeout duration for uploading file
    captcha_duration = settings['captcha_duration']  # Timeout duration for recaptcha test
 
def jsondump(data, file_path=accounts_path):
    with open(file_path, 'w') as F:
        json.dump(data, F, indent=4)
    return

# Set chromedriver name based on Operating System
if platform.system() == "Windows":
    chromedriver_name = "chromedriver.exe"
else:
    chromedriver_name = "chromedriver"


class SeleniumBot:
    def __init__(self, maingui, file_path, file_size):
        self.file_path = file_path
        self.file_size = file_size
        self.maingui = maingui

        self.maingui.printc(f"File Size Detected: {file_size} MB")

        # Fetch file paths and Define custom user agent (to prevent bot detection)
        chromedriver_path = Path(__file__).resolve().parent / chromedriver_name
        custom_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

        options = webdriver.ChromeOptions()
        options.add_argument(f'--user-agent={custom_user_agent}')

        service = Service(executable_path=chromedriver_path)
        self.driver = webdriver.Chrome(options=options, service=service)
        self.driver.maximize_window()

        self.maingui.printc("WebDriver Initialized")

    def waititem(self, path='', by='xpath', action='click', duration=wait_duration):
        if action == 'click':
            if by == 'xpath':
                item = WebDriverWait(self.driver, duration).until(
                    EC.element_to_be_clickable((By.XPATH, path)))
            elif by == 'id':
                item = WebDriverWait(self.driver, duration).until(
                    EC.element_to_be_clickable((By.ID, path)))
            item.click()
        elif action == 'send':
            if by == 'xpath':
                item = WebDriverWait(self.driver, duration).until(
                    EC.presence_of_element_located((By.XPATH, path)))
            elif by == 'id':
                item = WebDriverWait(self.driver, duration).until(
                    EC.presence_of_element_located((By.ID, path)))
            return item

    def upload(self):
        self.waititem('//button[@role="button" and @title="Open uploader" and @aria-label="Open uploader"]', 'xpath', 'click')
        self.waititem('//input[@type="file"]', 'xpath', 'send').send_keys(self.file_path)
        self.waititem('//button[@role="button" and @title="Begin upload" and @aria-label="Begin upload"]', 'xpath', 'click')

        self.maingui.printc("Uploading File")
        copybtn = WebDriverWait(self.driver, upload_duration).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@role="button" and @title="Copy link"]')))
        self.waititem('//div[@data-text-as-pseudo-element="Completed"]', 'xpath', 'send', upload_duration)
        self.maingui.printc("File Uploaded")
        copybtn.click()
        link = pyperclip.paste()
        return link

    def register(self, upload=True, name=('John', 'Doe')):
        # Get tempmail account
        tm = Email()
        tm.register()
        regmail = str(tm.address)
        password_length = random.randint(15, 29)
        regpass = secrets.token_urlsafe(password_length)

        self.maingui.printc("Generated TempMail Account")
        self.maingui.printc(f"Email: {regmail}")
        self.maingui.printc(f"Password: {regpass}")
        
        # Register in mediafire
        self.driver.get("https://www.mediafire.com/upgrade/registration.php?pid=free")

        self.waititem('reg_first_name', 'id', 'send').send_keys(name[0])
        self.waititem('reg_last_name', 'id', 'send').send_keys(name[1])
        self.waititem('reg_email', 'id', 'send').send_keys(regmail)
        self.waititem('reg_pass', 'id', 'send').send_keys(regpass)
        # Scroll down
        ActionChains(self.driver)\
            .scroll_to_element(self.waititem('signup_continue', 'id', 'send'))\
            .scroll_by_amount(0, 150)\
            .perform()
        
        self.waititem('agreement', 'id', 'click')

        # Attempt direct Registration (without Recaptcha)
        self.waititem('//*[@id="signup_continue"]', 'xpath', 'click', wait_duration)

        # Prompt to Solve Recaptcha
        self.maingui.printc("Please solve the reCaptcha test and press the Submit button if registration fails")
        try:
            # Wait for captcha to be completed
            self.waititem('//button[@role="button" and @title="Open uploader" and @aria-label="Open uploader"]', 'xpath', 'send', captcha_duration)
            self.maingui.printc("reCaptcha Test Successful")
        except:
            self.maingui.printc("reCaptcha Test Failed")
            self.maingui.pritnc("Account Registration Failed")
            return  # reCaptcha Failed. Cancel all Operations

        time.sleep(0.5)
        self.maingui.printc("Account Registered in MediaFire")

        if not upload:
            # Save account details in accounts.json
            details = {"email": regmail, "password": regpass, "free": 10000}
            with open(accounts_path, 'r+') as F:
                data = json.load(F)
                data.append(details)
                jsondump(data)
            return 'success'
        
        link = self.upload()
        print("Download Link: ", link)

        # Save details in accounts.json
        details = {"email": regmail, "password": regpass, "free": 10000 - self.file_size}
        with open(accounts_path, 'r+') as F:
            data = json.load(F)
            data.append(details)
            jsondump(data)
        self.maingui.printc("New Account Added to Database")
        return link

    def login(self, upload=True, det=('email', 'password')):
        email = ''
        password = ''
        with open(accounts_path, 'r+') as F:
            A = json.load(F)
            
            # Check if account database is empty
            if A == []:
                if upload == False:
                    return
                self.maingui.printc("No Accounts Found. Attempting Registration")
                link = self.register()
                if link is not None:
                    return link
                else:
                    return
                
            # Iterate through accounts to find one with required free storage    
            for i in A:
                if not i['free'] > self.file_size:
                    continue
                else:
                    if upload:
                        self.maingui.printc("Found Account with Required Free Storage")
                        email = i['email']
                        password = i['password']
                    else:
                        self.maingui.printc("Logging into Account")
                        email = det[0]
                        password = det[1]
                    self.driver.get('https://www.mediafire.com/login/')
                    self.waititem('widget_login_email', 'id', 'send').send_keys(email)
                    self.waititem('widget_login_pass', 'id', 'send').send_keys(password)
                    self.waititem('//button[@type="submit" and @class="gbtnTertiary"]', 'xpath', 'click')
                    time.sleep(0.5)
                    self.maingui.printc("Connected to Mediafire")
                    if not upload:
                        WebDriverWait(self.driver, wait_duration).until(
                            self.driver.current_url == 'https://app.mediafire.com/myfiles')
                        return 'success'
                    link = self.upload()
                    print("Download Link: ", link)

                    # Reduce the free space for the account
                    A[A.index(i)]['free'] -= self.file_size
                    jsondump(A)
                    self.maingui.printc("Account Storage Updated")
                    return link
                
            self.maingui.printc("No Accounts with Required Free Storage. Attempting Registration")    
            # No accounts with required free storage, then Register a new one
            link = self.register()
            if link is not None:
                return link  # Return download link
            else:
                return

class AccountsGUI:
    def __init__(self, maingui):
        self.root = tk.Tk()
        self.maingui = maingui

        # Define window size and title
        self.winheight = 800
        self.winwidth = 500
        self.root.geometry(f"{self.winheight}x{self.winwidth}")
        # root.resizable(False, False)
        self.root.title("Accounts")

        with open(accounts_path, 'r') as F:
            data = json.load(F)
            self.data = data

        # Define Elements
        self.mainframe = tk.Frame(self.root)

        topframe = tk.Frame(self.mainframe)

        addaccbtn = tk.Button(topframe, text="Add Account", command=self.addaccount)
        addaccbtn.grid(row=0, column=0, padx=10, pady=10)

        editaccbtn = tk.Button(topframe, text="Edit Accounts", command=self.editaccount)
        editaccbtn.grid(row=0, column=1, padx=10, pady=10)

        delaccbtn = tk.Button(topframe, text="Delete Account", command=self.delaccount)
        delaccbtn.grid(row=0, column=2, padx=10, pady=10)

        logaccbtn = tk.Button(topframe, text="Login", command=self.loginaccount)
        logaccbtn.grid(row=0, column=3, padx=10, pady=10)

        regaccbtn = tk.Button(topframe, text="Register Account", command=self.registeraccount)
        regaccbtn.grid(row=0, column=4, padx=10, pady=10)

        refaccbtn = tk.Button(topframe, text="Refresh Accounts", command=self.refresh_accounts)
        refaccbtn.grid(row=0, column=5, padx=10, pady=10)

        topframe.grid(row=0, column=0, padx=10, pady=10)

        self.create_table()

        self.mainframe.pack()
    
    def create_table(self, edit=False):
        # List to Hold Table Entries
        self.entries = []

        # Set Tableframe
        self.tableframe = tk.Frame(self.mainframe)
        self.tableframe.columnconfigure(0, weight=1, minsize=3)
        self.tableframe.columnconfigure(1, weight=1, minsize=200)

        # Create a canvas and scrollbar
        canvas = tk.Canvas(self.tableframe)
        scrollbar = tk.Scrollbar(self.tableframe, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add Table Headers
        headers = ["ID", "Address", "Password", "Storage"]
        for col, text in enumerate(headers):
            tk.Label(scrollable_frame, text=text, font=("Arial", 12)).grid(row=0, column=col, padx=10, pady=10)
        
        # Check if Edit mode is enabled
        _state = 'normal' if edit else 'readonly'

        # Add Table Entries
        for i, account in enumerate(self.data):
            row_entries = []
            for j in range(4):
                entry = tk.Entry(scrollable_frame, font=("Arial", 10))
                match j:
                    case 0:
                        entry.insert(0, str(i))
                        entry.config(width=3, state='readonly')
                    case 1:
                        entry.config(width=50)
                        entry.insert(0, account['email'])
                    case 2:
                        entry.insert(0, account['password'])
                    case 3:
                        entry.insert(0, f"{account['free']} MB")
                if not j == 0:
                    entry.config(state=_state)
                entry.grid(row=i+1, column=j, padx=2, pady=2, sticky='nw')
                row_entries.append(entry)  # Append column-wise entries (1D List)
            self.entries.append(row_entries)  # Append row-wise entries (2D List)
        
        # Place canvas and scrollbar in the tableframe
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tableframe.grid(row=1, column=0, padx=10, pady=10)

        # Adjust tableframe layout
        self.tableframe.grid_rowconfigure(0, weight=1, minsize=350)
        self.tableframe.grid_columnconfigure(0, weight=1, minsize=700)
        self.tableframe.grid_columnconfigure(1, weight=0, minsize=50)

        # Bind mousewheel to scroll the canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def addaccount(self):
        addwindow = tk.Toplevel(self.root)
        addwindow.geometry(f"400x150")
        addwindow.resizable(False, False)
        addwindow.title("Add Account")
        addwindow.grab_set()

        gridf = tk.Frame(addwindow)
        gridf.columnconfigure(0, weight=1)

        tk.Label(gridf, text="Email:").grid(row=0, column=0, padx=10, pady=10)
        self.email = tk.Entry(gridf, width=50)
        self.email.grid(row=0, column=1, padx=10, pady=10, sticky='nw')

        tk.Label(gridf, text="Password:").grid(row=1, column=0, padx=10, pady=10)
        self.password = tk.Entry(gridf)
        self.password.grid(row=1, column=1, padx=10, pady=10, sticky='nw')

        def saveaccount():
            email = self.email.get()
            password = self.password.get()
            if email == '' or password == '':
                mb.showinfo("Notice", "Please fill all fields")
                return
            else:
                details = {"email": email, "password": password, "free": 10000}
                self.data.append(details)
                jsondump(self.data)
                self.maingui.printc("Account saved successfully")
            self.refresh_accounts()
            addwindow.destroy()

        savebtn = tk.Button(gridf, text="Save", command=saveaccount)
        savebtn.grid(row=2, column=1, padx=10, pady=10, sticky='w')

        gridf.pack(anchor='nw')
    
    def editaccount(self):
        def saveedit():
            updated_data = []
            for i in self.entries:
                updated_data.append({
                    "email": i[1].get(),
                    "password": i[2].get(),
                    "free": int(i[3].get().split()[0])
                    })
            jsondump(updated_data)

            saveeditbtn.destroy()
            canceleditbtn.destroy()

            self.refresh_accounts()

        def canceledit():
            saveeditbtn.destroy()
            canceleditbtn.destroy()
            self.refresh_accounts()

        editbtnframe = tk.Frame(self.mainframe)
        saveeditbtn = tk.Button(editbtnframe, text="Save Changes", command=saveedit)
        canceleditbtn = tk.Button(editbtnframe, text="Cancel", command=canceledit)
        saveeditbtn.grid(row=0, column=0, padx=10, pady=10)
        canceleditbtn.grid(row=0, column=1, padx=10, pady=10)
        editbtnframe.grid(row=2, column=0, padx=10, pady=10)

        self.refresh_accounts(edit=True)

    def delaccount(self):
        def delete():
            def delconf():
                with open(accounts_path, 'r+') as F:
                    data = json.load(F)
                    try:
                        id = int(self.delentry.get())
                        data.pop(id)
                        jsondump(data)
                        self.maingui.printc("Account Deleted Successfully")
                    except:
                        self.maingui.notice("Invalid ID")
                self.refresh_accounts()
                delbtnframe.destroy()
                delconfwin.destroy()
            def delcancel():
                self.maingui.printc("Account Deletion Cancelled")
                self.refresh_accounts()
                delbtnframe.destroy()
                delconfwin.destroy()

            # Open Confirmation Dialog
            delconfwin = tk.Toplevel(self.root)
            delconfwin.geometry(f"300x100")
            delconfwin.resizable(False, False)
            delconfwin.title("Delete Account")
            delconfwin.grab_set()

            delconfframe = tk.Frame(delconfwin, padx=10, pady=10)
            delconfframe.columnconfigure(0, weight=1)

            delconflabel = tk.Label(delconfwin, text="Are you sure you want to delete this account?", font=("Arial", 10))
            delconflabel.pack()

            delconfbtn = tk.Button(delconfframe, text="Yes", font=("Arial", 10), command= delconf)
            delconfbtn.grid(row=0, column=0, padx=10, pady=10)

            delcancelbtn = tk.Button(delconfframe, text="No", font=("Arial", 10), command=delcancel)
            delcancelbtn.grid(row=0, column=1, padx=10, pady=10)

            delconfframe.pack(anchor='n')

        delbtnframe = tk.Frame(self.mainframe)

        dellabel = tk.Label(delbtnframe, text="Enter ID to delete: ", font=("Arial", 12))
        dellabel.grid(row=0, column=0, padx=10, pady=10)

        self.delentry = tk.Entry(delbtnframe, width=3, font=("Arial", 12))
        self.delentry.grid(row=0, column=1, padx=10, pady=10)

        delbtn = tk.Button(delbtnframe, text="Delete", font=("Arial", 12), command=delete)
        delbtn.grid(row=0, column=2, padx=10, pady=10)

        delbtnframe.grid(row=2, column=0, padx=10, pady=10)

    def loginaccount(self):
        def login():
            id = int(self.identry.get())
            if id >= len(self.data):
                self.maingui.notice("Invalid ID")
                return
            email = self.data[id]['email']
            password = self.data[id]['password']

            self.bot = SeleniumBot(self.maingui, '', -1)
            ret = self.bot.login(upload=False, det=(email, password))

            with open(settings_path, 'r') as F:
                settings = json.load(F)
            if settings['auto_logout'] == True:
                
                self.bot.driver.quit()

            if ret != 'success':
                self.maingui.notice("Login Failed")
            loginframe.destroy()
        loginframe = tk.Frame(self.mainframe)

        loglabel = tk.Label(loginframe, text="Enter ID to log into: ", font=("Arial", 12))
        loglabel.grid(row=0, column=0, padx=10, pady=10)

        self.identry = tk.Entry(loginframe, width=3, font=("Arial", 12))
        self.identry.grid(row=0, column=1, padx=10, pady=10)

        loginbtn = tk.Button(loginframe, text="Login", font=("Arial", 12), command=login)
        loginbtn.grid(row=0, column=2, padx=10, pady=10)

        cancelbtn = tk.Button(loginframe, text="Cancel", font=("Arial", 12), command=loginframe.destroy)
        cancelbtn.grid(row=0, column=3, padx=10, pady=10)

        loginframe.grid(row=2, column=0, padx=10, pady=10)

    def registeraccount(self):
        def reg():
            if self.fnameentry.get() == '':
                self.maingui.labelprint(self.fnameentry, "Johon")
            if self.lnameentry.get() == '':
                self.maingui.labelprint(self.lnameentry, "Doe")
            
            bot = SeleniumBot(self.maingui, '', 0)
            ret = bot.register(upload=False, name=(self.fnameentry.get(), self.lnameentry.get()))
            
            self.maingui.printc("Exiting WebDriver")
            bot.driver.quit()
            self.refresh_accounts()

            if ret == 'success':
                self.maingui.notice("Account Registered Successfully")
            else:
                self.maingui.notice("Account Registration Failed")
            regframe.destroy()

        regframe = tk.Frame(self.mainframe)

        reglabel1 = tk.Label(regframe, text="First Name: ", font=("Arial", 12))
        reglabel1.grid(row=0, column=0, padx=5, pady=10)

        self.fnameentry = tk.Entry(regframe, font=("Arial", 12))
        self.fnameentry.grid(row=0, column=1, padx=10, pady=10)

        reglabel2 = tk.Label(regframe, text="Last Name: ", font=("Arial", 12))
        reglabel2.grid(row=0, column=2, padx=5, pady=10)

        self.lnameentry = tk.Entry(regframe, font=("Arial", 12))
        self.lnameentry.grid(row=0, column=3, padx=10, pady=10)

        regbtn = tk.Button(regframe, text="Register", font=("Arial", 12), command=reg)
        regbtn.grid(row=0, column=4, padx=10, pady=10)

        reccancelbtn = tk.Button(regframe, text="Cancel", font=("Arial", 12), command=regframe.destroy)
        reccancelbtn.grid(row=0, column=5, padx=10, pady=10)

        regframe.grid(row=2, column=0, padx=10, pady=10)

    def refresh_accounts(self, edit=False):
        self.tableframe.destroy()
        with open(accounts_path, 'r') as F:
            self.data = json.load(F)
        self.create_table(edit)

class SettingsGUI:
    def __init__(self, maingui):
        self.root = tk.Tk()
        self.maingui = maingui

        # Define window size and title
        self.winheight = 300
        self.winwidth = 250
        self.root.geometry(f"{self.winheight}x{self.winwidth}")
        # root.resizable(False, False)
        self.root.title("Settings")

        # Define Elements
        self.mainframe = tk.Frame(self.root)
        self.mainframe.columnconfigure(0, weight=1)

        with open(settings_path, 'r') as F:
            self.settings = json.load(F)

        gridf = tk.Frame(self.mainframe)
        gridf.columnconfigure(0, weight=1)

        tk.Label(gridf, text="Wait Duration (s):", font=('Arial', 12)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.wait_duration = tk.Entry(gridf, width=10, font=('Arial', 12))
        self.wait_duration.insert(0, self.settings['wait_duration'])
        self.wait_duration.grid(row=0, column=1, padx=10, pady=10, sticky='ne')

        tk.Label(gridf, text="Upload Duration (s):", font=('Arial', 12)).grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.upload_duration = tk.Entry(gridf, width=10, font=('Arial', 12))
        self.upload_duration.insert(0, self.settings['upload_duration'])
        self.upload_duration.grid(row=1, column=1, padx=10, pady=10, sticky='ne')

        tk.Label(gridf, text="Captcha Duration (s):", font=('Arial', 12)).grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.captcha_duration = tk.Entry(gridf, width=10, font=('Arial', 12))
        self.captcha_duration.insert(0, self.settings['captcha_duration'])
        self.captcha_duration.grid(row=2, column=1, padx=10, pady=10, sticky='ne')

        tk.Label(gridf, text="Auto Logout: ", font=('Arial', 12)).grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.autologout = tk.BooleanVar(master=self.root, value=self.settings['auto_logout'])
        autologoutcheck = tk.Checkbutton(gridf, variable=self.autologout)
        autologoutcheck.grid(row=3, column=1, padx=10, pady=10, sticky='ne')

        def savesettings():
            self.settings['wait_duration'] = int(self.wait_duration.get())
            self.settings['upload_duration'] = int(self.upload_duration.get())
            self.settings['captcha_duration'] = int(self.captcha_duration.get())
            self.settings['auto_logout'] = bool(self.autologout.get())
            jsondump(self.settings, settings_path)
            self.maingui.printc("Settings Updated Successfully")
            self.root.destroy()

        savebtn = tk.Button(self.mainframe, text="Save", font=('Arial', 14), command=savesettings)
        savebtn.grid(row=1, column=0, padx=10, pady=10)

        gridf.grid(row=0, column=0, padx=10, pady=10)
        self.mainframe.pack()

        self.root.mainloop()

class MainGUI:
    def __init__(self):
        self.root = tk.Tk()

        # Define window size and title
        self.winheight = 800
        self.winwidth = 500
        self.root.geometry(f"{self.winheight}x{self.winwidth}")
        # root.resizable(False, False)
        self.root.title("Uplink Fire")

        # Define menubar
        self.menubar = tk.Menu(self.root)

        self.accountsmenu = tk.Menu(self.menubar, tearoff=0)
        self.accountsmenu.add_command(label="Open Accounts Window", command=self.accountsbtn)
        self.menubar.add_cascade(label="Accounts", menu=self.accountsmenu)

        self.settingsmenu = tk.Menu(self.menubar, tearoff=0)
        self.settingsmenu.add_command(label='View Settings', command=self.settingsbtn)
        self.menubar.add_cascade(label='Settings', menu=self.settingsmenu)

        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label='Get Help', command=self.helpbtn)
        self.menubar.add_cascade(label='Help', menu=self.helpmenu)

        self.root.config(menu=self.menubar)

        # Define Elements
        maingrid = tk.Frame(self.root)
        maingrid.columnconfigure(0, weight=1)
        maingrid.columnconfigure(1, weight=1)

        # Left Grid
        leftgrid = tk.Frame(maingrid)
        leftgrid.columnconfigure(0, weight=1)

        label1 = tk.Label(leftgrid, text="Select a file: ", font=("Arial", 15))
        label1.grid(row=0, column=0, padx=10, pady=10)

        self.filepathbox = tk.Entry(leftgrid, width=40, font=("Arial", 12))
        self.filepathbox.grid(row=1, column=0, padx=10, pady=5)

        browsebtn = tk.Button(leftgrid, text="Browse", font=("Arial", 10), command=self.browsefile)
        browsebtn.grid(row=1, column=1, padx=10, pady=5)

        uploadbtn = tk.Button(leftgrid, text="Upload", font=("Arial", 14), command=self.upload)
        uploadbtn.grid(row=2, column=0, padx=10, pady=10)

        linkframe = tk.Frame(leftgrid)
        linkframe.columnconfigure(0, weight=1)

        label2 = tk.Label(linkframe, text="Link: ", font=("Arial", 12))
        label2.grid(row=0, column=0, padx=5, pady=20)

        self.linkbox = tk.Entry(linkframe, width=40, font=("Arial", 10), state='readonly')
        self.linkbox.grid(row=0, column=1, padx=10, pady=20)

        linkcopybtn = tk.Button(linkframe, text="Copy", font=("Arial", 10), command=self.copylinkbtn)
        linkcopybtn.grid(row=0, column=2, padx=2, pady=20)

        linkframe.grid(row=3, column=0, padx=5, pady=10)

        forceQuittbn = tk.Button(leftgrid, text="Force Quit WebDriver", font=("Arial", 14), command=self.forcequit)
        forceQuittbn.grid(row=4, column=0, padx=10, pady=10)

        leftgrid.grid(row=0, column=0, sticky='nw')

        # Right Grid
        rightgrid = tk.Frame(maingrid)
        rightgrid.columnconfigure(0, weight=1)
        rightgrid.columnconfigure(1, weight=1)

        label3 = tk.Label(rightgrid, text="Log", font=("Arial", 15))
        label3.grid(row=0, column=0, padx=10, pady=10, sticky='n')

        self.log = tk.Text(rightgrid, height=24, width=40, font=("Arial", 10))
        self.log.grid(row=1, column=0, padx=10, pady=10, sticky='n')

        clearbtn = tk.Button(rightgrid, text="Clear log", font=("Arial", 10), command=lambda: self.log.delete(1.0, tk.END))
        clearbtn.grid(row=2, column=0, padx=10, pady=10, sticky='n')

        rightgrid.grid(row=0, column=1, sticky='ne')

        maingrid.pack()

        self.root.mainloop()
    
    def printc(self, text):
        self.log.insert(tk.END, text + "\n")
    def labelprint(self, label, text):
        label.delete(0, tk.END)
        label.insert(0, text)
    def notice(self, message, title="Notice"):
        mb.showinfo(title, message)

    def browsefile(self):
        path = str(Path(fd.askopenfilename()))
        self.labelprint(self.filepathbox, path)
        self.log.insert(tk.END, "Added file:  " + path + "\n")
        self.path = path

    def upload(self):
        fpb = str(Path(self.filepathbox.get()))
        if fpb == '':
            self.notice("Please select a file to upload!")
            return
        else:
            self.path = fpb
            self.printc('File path updated!')

        if not os.path.exists(self.path):
            self.notice("File path does not exist!")
            return

        file_size = os.path.getsize(self.path) // 1000000  #Convert to MB
        
        bot = SeleniumBot(self, self.path, file_size)
        link = bot.login()
        self.printc('Exiting WebDriver')
        bot.driver.quit()
        if link is not None:
            self.linkbox.config(state='normal')
            self.labelprint(self.linkbox, str(link))
            self.linkbox.config(state='readonly')

            self.notice("File uploaded successfully!")
        else:
            self.printc("File Upload Failed")
            self.notice("File upload failed")

    def copylinkbtn(self):
        pyperclip.copy(self.linkbox.get())
        self.notice("Link copied to clipboard!")

    def forcequit(self):
        try:
            if hasattr(self, 'bot') and self.bot.driver:
                self.bot.driver.quit()
                self.printc('WebDriver quit successfully')
            else:
                self.notice("WebDriver not Detected")
        except webdriver.WebDriverException as e:
            self.notice(f"Error quitting WebDriver: {str(e)}")
        except Exception as e:
            self.notice(f"An unexpected error occurred: {str(e)}")

    def accountsbtn(self):
        self.accountsgui = AccountsGUI(self)

    def settingsbtn(self):
        settingsgui = SettingsGUI(self)

    def helpbtn(self):
        helpwin = tk.Toplevel(self.root)
        helpwidth = 500
        helpheight = 300
        helpwin.geometry(f"{helpwidth}x{helpheight}")
        helpwin.title("Help")
        helpwin.grab_set()
        
        helptxt = (
        "IMPORTANT: If the webdriver is not working properly, download the latest (stable) version of chromedriver.exe from https://googlechromelabs.github.io/chrome-for-testing/ and replace the old one in the _internal folder with the new one. Make sure to rename it as chromedriver in case the name is different.\n\n\n"
        "Select a File to Upload\n\n"
        "Wait for the WebDriver to complete Upload before changing Active Window\n\n"
        "The Link can be Shared to anyone for Downloading the File\n\n"
        "If there are no Accounts left with required storage, the WebDriver tries to Register a new one\n\n"
        "While Account Registration, Fill the reCAPTCHA test yourself and click the Submit button if automatic registration fails. The program should continue by itself after that\n\n"
        "In manual Registration, an empty name results in 'John Doe' as default\n\n"
        "If an account has been suspended due to inactivity, it is recommended to delete it\n\n"
        "To Prevent account suspension, log into the account at least once every year\n\n"
        "Tip: Files bigger than 10 GB can not be uploaded\n\n"
        "Wait Duration refers to the maximum time the WebDriver waits for checking components, only increase it in case you have a very slow internet\n\n"
        "Upload Duration refers to the maximum Time allotted to File Uploading. If a file takes longer than that to upload, it will be interrupted\n\n"
        "Captcha duration refers to the maximum Time given to the user for filling the recaptcha and submitting (only in Registration)"
        )
        helptext = scrolledtext.ScrolledText(helpwin, wrap=tk.WORD, font=("Arial", 10), padx=10, pady=10)
        helptext.insert(tk.INSERT, helptxt)
        helptext.config(state=tk.DISABLED)
        helptext.pack(expand=True, fill='both')

maingui = MainGUI()
