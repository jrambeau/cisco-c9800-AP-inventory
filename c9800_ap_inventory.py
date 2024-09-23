import logging
from c9800 import C9800
import argparse
import pandas as pd
import datetime
import getpass
import openpyxl
import os

## Set logging level and format
logging.basicConfig(level=logging.INFO, format="%(asctime)-15s (%(levelname)s) %(message)s")

## Parse command line arguments.
# parser = argparse.ArgumentParser(description="Utility to build .xls and .csv AP inventory from C9800")
# parser.add_argument('-user', help='c9800 username', required=True)
# parser.add_argument('-password', help='c9800 password', required=True)
# parser.add_argument('-wlc_ip', help='c9800 IP address', required=True)
# args=parser.parse_args()

# Liste des IP des contrôleurs
iplist = open('devices_ip_list.txt','r').read().splitlines()

# Login
un = input('Username: ')
pw = getpass.getpass()

devices = [] # Empty array to store controllers

for ip in iplist:
    # Create an object of type C9800 and store it in the wlc variable
    devices.append(C9800(ip, un, pw))

for wlc in devices:
    # Get hostname for export files
    wlc.get_hostname()

    logging.info(f"Dealing with controller {wlc.controller_hostname}")
    aps = wlc.get_joined_aps()

    if aps!=0: # Check if the controller actually has APs joined. If not, we do not create the inventory files.
        # Convert AP dictionnary into dataframe
        df = pd.DataFrame(aps).T

        # Write files
        dir = "inventory"
        subdir = wlc.controller_hostname
        filename = wlc.controller_hostname + "_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_AP-Inventory"
        full_path_file = os.path.join(dir, subdir, filename)
        os.makedirs(os.path.dirname(full_path_file), exist_ok=True)

        df.to_excel(full_path_file+".xlsx", index=False)
        df.to_csv(full_path_file+".csv", index=False)

    # Recupération de la configuration en API. NON FONCTIONNEL, utiliser le script netmiko
    """
    # Get running-configuration
    config = wlc.get_configuration()

    # Save running-configuration to file
    dir = "configuration"
    subdir = wlc.controller_hostname
    filename = wlc.controller_hostname + "_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".conf"
    full_path_file = os.path.join(dir, subdir, filename)
    os.makedirs(os.path.dirname(full_path_file), exist_ok=True)
    with open(full_path_file, "w") as file:
        file.write(config)
    """

logging.info(f"Done")
