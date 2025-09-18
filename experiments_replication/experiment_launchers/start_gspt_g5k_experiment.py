import os

config_file = "../RESULTS_GSPT/staging/config.yml"
if os.path.isfile(config_file):
    print("##################################################")
    print("# A config already exists in the staging folder! #")
    print("# A config already exists in the staging folder! #")
    print("# A config already exists in the staging folder! #")
    print("##################################################")
    exit(1)

gspt_dir = "YOUR GREENSPECTOR INSTALL DIR"
gspt_script = "grid5000.testgb"

with open(gspt_dir+gspt_script) as file:
    contents = file.read()
    if "browserGoToUrl,${STENDPOINT}" not in contents:
        print("##################################################")
        print("#  STENDPOINT variable missing from gdsl script  #")
        print("#  STENDPOINT variable missing from gdsl script  #")
        print("#  STENDPOINT variable missing from gdsl script  #")
        print("##################################################")
        exit(1)


import logging
import time
from datetime import datetime

from pathlib import Path
import g5k

import subprocess
import yaml

import sys
import re

import enoslib as en

skipg5k = False
proxy = ""
seektune_version = "PLACEHOLDER"
if len(sys.argv) > 2:
    if sys.argv[1] == "skipg5k":
        skipg5k = True
        proxy = sys.argv[2]
        print( "##################################################")
        print( "  Skipping G5K setup  ")
        print( "    Proxy URL:      ")
        print(f"    {proxy}   ")
        print( "    DONT FORGET TO PUT THE SEEKTUNE \n" \
               "    VERSION IN THE CONFIG FILE")
        print( "##################################################")

print("Waiting 10 sec before starting...")
time.sleep(10)

if not skipg5k:
    en.init_logging(level=logging.INFO)

    en.check()

    cluster = "paradoxe"
    seektune_version = "saas"
    (conf, provider) = g5k.configure_enoslib(en, cluster)

    (roles, st_server_adress, st_node, env_line, site, cors, proxy) = g5k.reserve_resources(provider)

    print(st_server_adress)

    g5k.deploy_st(seektune_version, roles, en, site, cors, env_line)

# -------- GSPT --------

environments = [
    "mobile::android::8::Samsung - Galaxy S7",
    "mobile::android::10::Samsung - Galaxy S9",
    "mobile::android::10::Samsung - Galaxy S9",
    "mobile::android::10::Samsung - Galaxy S9",
    "mobile::android::13::Samsung - Galaxy S22",
    "mobile::android::13::Samsung - Galaxy Tab S7 FE",
    "mobile::android::12::Samsung - Galaxy S10",
    "mobile::android::12::Samsung - Galaxy S10",
    "mobile::android::14::Samsung - Galaxy S22",
]

network_modes = [
    "WIFI", "4G", "3G", "2G"
]

selected_env = environments[8]
(platform, os, version, device) = selected_env.split("::")

network_mode = network_modes[0]

index = 8
proxy = proxy[:index] + "g5kid:g5kpass@" + proxy[index:]

cmd_args = ["gspt", "testbench", "set-environment", "-e", selected_env]
subprocess.run(cmd_args, cwd=gspt_dir)

cmd_args = f'gspt testbench custom-tests --testsSuite launch:./{gspt_script} --monitoredPackage "com.android.chrome" --iterations=1 --disable-dumpsys -e config-skipsetupphone=false --networkMode={network_mode} -e PAUSEDURATION=30000 -e PAUSEAFTERLOAD=1000 -e STENDPOINT={proxy}'.split(" ")
subprocess.run(cmd_args, cwd=gspt_dir)

gspt_config = {
    'time': datetime.now(),
    'node': re.search(r"[a-z]*-\d+", proxy)[0],
    'mode': seektune_version,
    'network': network_mode,
    'environment': {
        'platform': platform,
        'os': os,
        'version': version,
        'device': device,
    }
}

with open(config_file, "a") as conf:
    yaml.dump(gspt_config, conf, default_flow_style=False)

import requests
# Constants
BASE_URL = "https://core-saas-prod.greenspector.com"

def load_bearer_token(token_path="token.txt"):
    """Read bearer token from a text file."""
    with open(token_path, "r") as f:
        return f.read().strip()  # Remove any trailing whitespace/newline

def fetch_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {load_bearer_token()}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

finished = False
ctr = 0 # Bc the api is not reliable
while not finished and ctr<2:
    time.sleep(30)
    res = fetch_json("/api/testbench/jobs/running?offset=0&size=10")
    finished = len(res["results"]) == 0
    if finished:
        ctr = ctr+1
    else:
        ctr=0
    print(f"[{ctr}] Test running...")

print("Test finished!")