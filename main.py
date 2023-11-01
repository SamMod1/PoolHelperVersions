PROGRAM_NAME = """
██████╗░░█████╗░░█████╗░██╗░░░░░  ██╗░░██╗███████╗██╗░░░░░██████╗░███████╗██████╗░
██╔══██╗██╔══██╗██╔══██╗██║░░░░░  ██║░░██║██╔════╝██║░░░░░██╔══██╗██╔════╝██╔══██╗
██████╔╝██║░░██║██║░░██║██║░░░░░  ███████║█████╗░░██║░░░░░██████╔╝█████╗░░██████╔╝
██╔═══╝░██║░░██║██║░░██║██║░░░░░  ██╔══██║██╔══╝░░██║░░░░░██╔═══╝░██╔══╝░░██╔══██╗
██║░░░░░╚█████╔╝╚█████╔╝███████╗  ██║░░██║███████╗███████╗██║░░░░░███████╗██║░░██║
╚═╝░░░░░░╚════╝░░╚════╝░╚══════╝  ╚═╝░░╚═╝╚══════╝╚══════╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝
"""
VERSION = 'Dev 2.0 Sim'
"""
This is a re-write of the Pool Helper analysis program. The aim of this re-write is to write in new features, make the script object-orientated 
and make it more efficient.

Shared drive: \\strjupiterflproduks01.file.core.windows.net\limsextract\poolHelper

TODO        
    Try to make the quadrant heatmaps all change using one set of buttons
    
    Give the reagents used
            
    Look into nexar tip patterns
    
    See if the barcode platemaps can be made with consistent colour formatting within the same plate
    
    Impliment colour formatting rules for ROX heatmap
            
    Version 3?:
    - Look through Lizzie's case studies and think about how Pool Helper might be able to use these
    - Individual CV for each well
"""

import os
import sys
import pandas as pd
import src.functions as f
from getpass import getpass
from src.analysis import Analysis
from sim.generateModel import Simulator


CONFIG_FILE = 'config.txt'
CURRENT_VERSION_FILE = "version.txt"


# Not strictly necissary, but prevents Spyder from thinking there is a bunch of errors:
GLOBALS = None
ADMINS = None
THRESHOLDS = {}
POSITIVES_TO_GEN = (1, 93)  # The range of true positives per plate this analysis should consider
PLATES_TO_GEN = 50000  # How many plates to generate for each number of positives in the range POSITIVES_TO_GEN
PLATE_DIMENSIONS = (8, 12)  # Dimensions for the microplate array. E.g. (8, 12) for 96 well plates, (24, 16) for 384 well plates
CONTROL_POSITIONS = ((8, 10), (8, 11), (8, 12))  # The locations on plates which contain any control wells
CHANNEL_POSITIVITY = 0.4  # Positivity rate for the testing channel of interest


class PoolHelper:
    def __init__(self, version):
        self.check_version()
        self.lims_pass = 'lims_pass'
        self.thresholds_pass = 'config_pass'
        self.p_thresholds = pd.read_csv('.//sim//thresholds.csv')
        self.alpha = self.p_thresholds['p'][0]
        self.connection = None
        self.cur = None
        self.thresholds = None
        self.offline = False
        self.admin = False
        self.username = None
        self.globals = None
        self.globals_split = None
        self.get_globals()
        self.lims_login()
        self.menus()
        
    def login_failed(self):
        inp = input("""
Could not log into the LIMS mirror
Press enter to save your credentials securely
Or 
Type 'OFFLINE' to enter offline mode: """)
        if inp == 'OFFLINE':
            self.offline = True
            warning = """WARNING:
    In offline mode many features will not work properly, this mode should not be 
    used for data reporting unless given prior authorisation
    Do you wish to continue?"""
            f.give_warning(warning)
            self.menus()
        else:
            self.lims_login_modify()

    def check_version(self):
        if VERSION[0:3] == 'Dev':
            print('Version: ' + VERSION)
            print("""WARNING: This is a development version and shouldn't be used for reporting""")    
        else:
            try:
                with open(CURRENT_VERSION_FILE, 'r') as file:
                    latest_version = file.read()
                if VERSION != latest_version:
                    print(VERSION + '\n')
                    f.give_warning(f"""WARNING: 
        This is not the latest version of Pool Helper.
        Only the latest version may be used for data reporting
        This version: {VERSION}
        Latest version: {latest_version}
        Do you wish to continue?""")
                else:
                    print(f"{VERSION} (latest)")
            except (FileNotFoundError, PermissionError):
                f.give_warning(f"""WARNING: 
        This version: {VERSION}
        Cannot determine if this is the latest version
        This could be because you do not have permissions
        necissary to run Pool Helper, please contact
        either Joshua Modern or Elizabeth May Bolitho""", serious_error = True)
    
    def lims_login(self):
        self.admin = False
        try:
            if False:#try:
                encrypted = os.getenv('LIMS_MIRROR_CREDENTIALS')
                if encrypted == None:
                    self.login_failed()
                decrypted = f.decrypt(self.lims_pass, encrypted.encode())
                credentials = decrypted.decode().split('£$%')
                self.username = credentials[0]
                self.connection = None# cx_Oracle.connect(user=self.username,password=credentials[1],dsn="LIMSREP")
                self.connection.current_schema = 'VGSM'
                self.cur = self.connection.cursor()
                print('\n')
                if self.username in ADMINS:
                    self.admin = True
                    print('You are an admin user')
                print("LIMS login successful")
            if True:# except cx_Oracle.DatabaseError:
                    self.login_failed()
        except AttributeError:
            self.login_failed()
            
    def lims_login_modify(self):
        new_username = input("""Input the username to save: """)
        new_password = getpass("Password: ")
        message = f"""{new_username}£$%{new_password}"""
        encrypted = f.encrypt(self.lims_pass, message)
        os.system(f"setx LIMS_MIRROR_CREDENTIALS {encrypted.decode()}")  # For later
        f.give_warning("""Your login credentials have been encrypted and saved. You need to restart this program""", serious_error = True)
       
    def get_globals(self):
        try:
            with open(CONFIG_FILE, 'rb') as file:
                encrypted = file.read()
        except (FileNotFoundError, PermissionError):
                f.give_warning("""ERROR: 
Could not access the shared drive: \\strjupiterflproduks01.file.core.windows.net\limsextract\poolHelper
Access to this drive is needed for the program to run properly. Please request access to the required drive.
        """, serious_error = True)
        decrypted = f.decrypt(self.thresholds_pass, encrypted)
        self.globals = decrypted.decode()
        exec(self.globals)
        self.globals_split = self.globals.split('#split')
        self.thresholds = self.globals_split[1]
        
       
    def modify_threshold(self):
        if self.admin:
            print(self.thresholds)
            threshold = input('Which threshold do you want to modify\n(type name of threshold exactly): ')
            try:
                new_value = input('What should the new value be: ')
                float(new_value)
            except ValueError:
                print('\nError, input was not numeric\n')
                self.menus()
            try:
                self.globals = self.globals.replace(threshold + ' = ' + str(THRESHOLDS[threshold]), threshold + ' = ' + str(new_value))
            except KeyError:
                print("Error: Input threshold did not match any existing thresholds")
                self.menus()
            encrypted = f.encrypt(self.thresholds_pass, self.globals)
            with open('config.txt', 'wb') as file:
                file.write(encrypted)
            exec(self.globals)
            self.globals_split = self.globals.split('#split')
            self.thresholds = self.globals_split[1]
            print('\nNew thresholds:\n' + self.thresholds)
            self.menus()
        else:
            print("Only admins can do this!")
    
    def modify_p(self):
        print(f'The current p-value is set to {self.p_thresholds["p"][0]}')
        try:
            p = input("Enter a new p-value to save: ")
            sim = Simulator(PLATE_DIMENSIONS, POSITIVES_TO_GEN, CONTROL_POSITIONS, PLATES_TO_GEN)
            print('\nAnalysing simulation...')
            self.p_thresholds = pd.DataFrame(sim.get_p_thresholds(alpha_value = float(p), filepath = './/sim//'))
            self.p_thresholds['p'] = p
            self.p_thresholds.to_csv('.//sim//thresholds.csv', index = False)
            self.alpha = float(p)
        except ValueError:
            print('\nERROR: p-values must be numeric!\n')
        self.menus()
    
    def menus(self):
        print("""
\nMain Menu
--------------------------------------------------------------
To see a list of commands enter 'help'
To run a batch of plates enter 'r'
To exit the program enter 'q'""")
        while True:
            inp = input('\ninput: ')
            if inp.lower() == 'help':
                print("""
\nMain Menu Commands
--------------------------------------------------------------
'help'      : This page
'r'         : Run a batch of plates
'rf'        : Run a batch of plates from files in the Araya Files folder
'q'         : Quits the program
'login'     : Modify and save your LIMS login information
'thresholds': View the current thresholds
'admins'    : View admin users
'p'         : Modifies the p-value used for designating patterns as suspicious
'update'    : (admin) Modify a threshold for all users
'radmin'    : (admin) Runs a plate with the option to choose the araya
'rfadmin'   : (admin) Run from files as admin
    """)
            elif inp.lower() == 'r':
                if self.offline:
                    print("This is not available in offline mode, use 'rf' to run from the araya files directly")
                else:
                    self.analyse()
            elif inp.lower() == 'rf':
                self.analyse(from_files = True)
            elif inp.lower() == 'q':
                sys.exit()
            elif inp.lower() == 'login':
                self.lims_login_modify()
            elif inp.lower() == 'update':
                self.modify_threshold()
            elif inp.lower() == 'p':
                self.modify_p()
            elif inp.lower() == 'thresholds':
                print(self.thresholds)
            elif inp.lower() == 'admins':
                print(self.globals_split[2])
            elif inp.lower() == 'radmin':
                self.analyse(as_admin = True)
            elif inp.lower() == 'rfadmin':
                self.analyse(from_files = True, as_admin = True)
            else:
                print("Input did not match any of the menu options. Type 'help' to see all options\n")
                
    def analyse(self, from_files = False, as_admin = False):
        if as_admin and not self.admin:
            print("Only admins can do this!")
            self.menus()
        if self.cur == None:
            self.analysis = Analysis(VERSION, None, GLOBALS, THRESHOLDS, None, self.p_thresholds, self.alpha, PLATES_TO_GEN, admin = True, from_files = True, mirrorless = True)
        elif not from_files:
            try:
                plate = input('Enter the Tape ID of one plate in the batch: ')
                int(plate)
            except ValueError:
                print('\nERROR: Input must be a number')
                self.menus()
            try:
                self.analysis = Analysis(VERSION, plate, GLOBALS, THRESHOLDS, self.cur, self.p_thresholds, self.alpha, PLATES_TO_GEN, admin = as_admin)
            except (UnboundLocalError, IndexError):
                print('\nERROR: Something went wrong! The plate you entered may not be in LIMS')
                self.menus()
        else:
            self.analysis = Analysis(VERSION, None, GLOBALS, THRESHOLDS, self.cur, self.p_thresholds, self.alpha, PLATES_TO_GEN, admin = as_admin, from_files = True)
        self.analysis.run_analysis()
    

if __name__ == '__main__':
    print(PROGRAM_NAME)
    program = PoolHelper(VERSION)
