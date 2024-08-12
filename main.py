from subprocess import run,Popen,PIPE
from os import geteuid,listdir
from os.path import join as join_path
from typing import List,Tuple

ROOT = geteuid() == 0
CLUSTER_DIR = "/sys/devices/system/cpu/cpufreq"
SET_MAX_FREQ_FILE = "/proc/ppm/policy/hard_userlimit_max_cpu_freq"
SET_MIN_FREQ_FILE = "/proc/ppm/policy/hard_userlimit_min_cpu_freq"
NO_ROOT = "you can't run this without root"
NO_SUPPORT = "your device doesn't support this script."

def prun(cmd : str):
    return run(cmd,shell=True,capture_output=True)

if not ROOT:
    print(NO_ROOT)
    exit()

# enable ppm
result = prun("echo 1 >/proc/ppm/enabled")
if result.returncode != 0:
    print("{} /proc/ppm/enabled not found".format(NO_SUPPORT))
    exit()

# list all clusters
clusters: List[str] = []
clusters_freq  : List[List[int]] = []
for cluster in listdir(CLUSTER_DIR):
    # sort clusters
    number = int(cluster[6:])
    clusters.insert(number,cluster)

for cluster_id,cluster in enumerate(clusters):
    try:
        freqs_file = open(join_path(CLUSTER_DIR,cluster,"scaling_available_frequencies"),"r")
    except:
        print("{} scaling_available_frequencies not found".format(NO_SUPPORT))
        exit()

    freqs = freqs_file.read().split(" ")[:-1]
    clusters_freq.insert(cluster_id,[])
    for freq in freqs:
        clusters_freq[cluster_id].append(int(freq))
# begin gui
class BUTTON_CODE:
    BACK = 3
    EXIT = 1

def radiolist(name : str, options : List[any]) -> Tuple[str | None,int]:
    args = []
    for entry in options:
        args.append("'{}' '' 0 ".format(entry))
    
    built_command = "dialog --cancel-label 'Quit' --extra-button --extra-label 'Back' --radiolist '{}' 0 0 0 {} ".format(name,"".join(args))
    dialog = Popen(built_command,shell=True,stderr=PIPE)
    _,result = dialog.communicate()

    result = result.decode()
    
    if result == "":
        result = None
        
    return result,dialog.returncode

def select_cluster() -> Tuple[int | None,int]:

    cluster_index = []

    for index,_ in enumerate(clusters_freq):
        cluster_index.append(index)
    
    result,return_code = radiolist("Select Cluster",cluster_index)

    if not result:
        result = None
    else:
        result = int(result)

    return result,return_code

def select_freq_type() -> Tuple[str | None,int]:
    return radiolist("Select Frequency Type",["min","max"])

def select_freq(cluster_id : int, extra : str) -> int | None:
    result,return_code = radiolist("Select {} Frequency".format(extra),clusters_freq[cluster_id])
    
    if not result:
        result = None
    else:
        result = int(result)

    return result,return_code

func = 0
cluster = 0
freq_type = ""
return_code = 0
min_freq = 0
max_freq = 0

def inc(bool : any):
    if bool == None:
        return func
    return func + 1

while True:

    match return_code:
        case BUTTON_CODE.BACK:
            func -=1
        case BUTTON_CODE.EXIT:
            quit()

    return_code = 0

    match func:
        case 0:
            cluster,return_code = select_cluster()
            func = inc(cluster)
        case 1:
            min_freq,return_code = select_freq(cluster,"Minimum")
            func = inc(freq_type)
        case 2:
            max_freq,return_code = select_freq(cluster,"Maximum")
            func = inc(freq_type)
        case 3:
            prun("echo {} {} > {}".format(cluster,max_freq,SET_MAX_FREQ_FILE))
            prun("echo {} {} > {}".format(cluster,min_freq,SET_MIN_FREQ_FILE))
            func = inc(True)
        case default:
            func = 0
            continue