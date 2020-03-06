import os
import sys
import re
import json
import logging
import logging.handlers
import subprocess
import timeit
try:
    import urllib2
except ImportError:
    # Since Python 3, urllib2.Request and urlopen were moved to
    # the urllib.request.
    import urllib.request as urllib2
#===============================================================================
def initialize(args, module):
# License types:
# 0 - Unknown
# 1 - Trial
# 2 - Subscription
# 3 - Permanent

    #Initializing variables
    sys_dir = "/var/tom" #All working data (tmp, logs,...) will be here
    sys_name = "tom" #Codename for all collection of CROC scripts
    #module_name is needed for creating directory for logs and tmp files
    module_name = ''.join((sys_name, module["subname"]))
    module_loglevel = logging.INFO #Default
    module_logfilesize = 512*1024 #Default
    module_logfilecount = 4 #Default
    zabbix_api_url = "http://localhost/zabbix/api_jsonrpc.php" #Default
    zabbix_api_user = "apiuser" #Default
    zabbix_api_password = "apipassword" #Default
    zabbix_externalscripts_dir = "/usr/lib/zabbix/externalscripts" #Default
    zabbix_sender_command = "/usr/bin/zabbix_sender" #Default
    zabbix_agent_config_path = "/etc/zabbix/zabbix_agentd.conf" #Default
    device_default_login = "zabbix:zabbix"
    device_tzshift = 0
    device_timestring = "%Y-%m-%d %I:%M:%S"
    sys_logdir = '/'.join([sys_dir, "logs"])
    sys_tmpdir = '/'.join([sys_dir, "tmp"])
    module_logdir = '/'.join([sys_logdir, module_name])
    module_tmpdir = '/'.join([sys_tmpdir, module_name])

    settings_file = "/var/tom/settings"

    #If debug mode is needed
    if args.debug:
        module_loglevel = logging.DEBUG
    
    #Checking if settings and license files exist
    if not os.path.exists(settings_file):
        print("ERROR: settings file not found!")
        return False

    #Creating working directories
    if not os.path.exists(sys_logdir):
        os.makedirs(sys_logdir)
    if not os.path.exists(sys_tmpdir):
        os.makedirs(sys_tmpdir)
    if not os.path.exists(module_logdir):
        os.makedirs(module_logdir)
    if not os.path.exists(module_tmpdir):
        os.makedirs(module_tmpdir)

    with open(settings_file, "r") as f:
        for line in f:
            #Settings line must be in format "key = value"
            string = re.search(r"^(.+)\s=\s(.+)", line)
            if not string:
                #Check if line is comment
                string = re.search("^#", line)
                if string:
                    continue
                else:
                    print("ERROR: Settings file is corrupted")
                    return False
            if string.group(1) == "zabbix_externalscripts_dir":
                zabbix_externalscripts_dir = string.group(2)
            elif string.group(1) == "zabbix_sender_command":
                zabbix_sender_command = string.group(2)
            elif string.group(1) == "zabbix_agent_config_path":
                zabbix_agent_config_path = string.group(2)
            elif string.group(1) == "zabbix_api_url":
                zabbix_api_url = string.group(2)
            elif string.group(1) == "zabbix_api_user":
                zabbix_api_user = string.group(2)
            elif string.group(1) == "zabbix_api_password":
                zabbix_api_password = string.group(2)
            elif string.group(1) == "logfile_size":
                module_logfilesize = int(string.group(2))*1024
            elif string.group(1) == "logfile_count":
                module_logfilecount = int(string.group(2))
            elif string.group(1) == '.'.join(
                ["logfile_size", module_name]):
                module_logfilesize = int(string.group(2))*1024
            elif string.group(1) == '.'.join(
                ["logfile_count", module_name]):
                module_logfilecount = int(string.group(2))
            #Default user for connecting to device
            elif string.group(1) == "device_user":
                device_user = string.group(2)
                str_user = re.search("(.+);(.+)", device_user)
                if str_user.group(1) == "text":
                    device_default_login = str_user.group(2)
            #User for connecting to individual device
            elif string.group(1) == "device_user.%s" % args.agentid:
                device_user = string.group(2)
                str_user = re.search("(.+);(.+)", device_user)
                if str_user.group(1) == "text":
                    device_default_login = str_user.group(2)

    env = {
        "sys_dir" : sys_dir,
        "sys_name" : sys_name,
        "module_name" : module_name,
        "module_loglevel" : module_loglevel,
        "module_logfilesize" : module_logfilesize,
        "module_logfilecount" : module_logfilecount,
        "zabbix_externalscripts_dir" : zabbix_externalscripts_dir,
        "zabbix_sender_command" : zabbix_sender_command,
        "zabbix_agent_config_path" : zabbix_agent_config_path,
        "zabbix_api_url" : zabbix_api_url,
        "zabbix_api_user" : zabbix_api_user,
        "zabbix_api_password" : zabbix_api_password,
        "device_default_login" : device_default_login,
        "device_tz_shift" : device_tzshift,
        "device_timestring" : device_timestring,
        "sys_logdir" : sys_logdir,
        "sys_tmpdir" : sys_tmpdir,
        "module_logdir" : module_logdir,
        "module_tmpdir" : module_tmpdir,
        }
    #Appending specific module properties like
    #device_namespace, supported_models
    env.update(module)

    #print(env)
    return env
#===============================================================================
def log_exception_handler(type, value, tb):
    logger = logging.getLogger('tom')
    logger.exception("Uncaught exception: {0}".format(str(value)))
#===============================================================================
def setup_logging(env, logfile):
    module_logger = logging.getLogger('tom')
    module_logger.setLevel(env["module_loglevel"])

    handler = logging.handlers.RotatingFileHandler(
                          logfile,
                          maxBytes=env["module_logfilesize"],
                          backupCount=env["module_logfilecount"]-1)

    formatter = logging.Formatter(
        ' '.join(['[%(asctime)s]',
                  '%(levelname)s',
                  '[%(process)d - %(threadName)s]',
                  '%(message)s'])
        )
    handler.setFormatter(formatter)
    module_logger.addHandler(handler)
    sys.excepthook = log_exception_handler
    return
#===============================================================================
def colonify_wwn(WWN):
    return ':'.join((WWN[0:2],WWN[2:4],WWN[4:6],WWN[6:8],
                     WWN[8:10],WWN[10:12],WWN[12:14],WWN[14:16]))
#===============================================================================
def zabbix_output(data):
    logger = logging.getLogger('tom')
    logger.info("Generating output for Zabbix")

    output = json.dumps({"data": data}, indent=4, separators=(',', ': '))
    logger.info(output)
    logger.info("Done!")

    return output
#===============================================================================
def zabbix_send_data(env, nodename, data, filename):
    logger = logging.getLogger('tom')
    logger.info("Sending data to ZABBIX")

    zabbix_sender_command = env["zabbix_sender_command"]
    zabbix_agent_config_path = env["zabbix_agent_config_path"]

    logger.info("ZABBIX sender: %s" % zabbix_sender_command)
    logger.info("ZABBIX agent config path: %s" % zabbix_agent_config_path)

    if not os.path.exists(zabbix_agent_config_path):
        logger.error("Agent config file does not exist!")
        print("Agent config file does not exist!")
        return

    with open(filename, "w") as f:
        f.write(str(data))

    try:
        subprocess.call([zabbix_sender_command, "-v", "-c",
                            zabbix_agent_config_path,
                            "-s", nodename, "-T", "-i", filename])

    except:
        logger.error("Can not send data to ZABBIX")
        return
    logger.info("Data were sent to ZABBIX")
#===============================================================================
def zabbix_request(url, method, params, auth):
    funcstart = timeit.default_timer()
    logger = logging.getLogger('tom')
    logger.info("Sending request to ZABBIX")
    
    request_json = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
        "auth": auth
    }

    request = json.dumps(request_json, indent=4, separators=(',', ': '))
    if not isinstance(request, bytes):
        request = request.encode("utf-8")

    logger.debug("Request:\n%s" % request)

    req = urllib2.Request(url, request)
    req.get_method = lambda: 'POST'
    req.add_header('Content-Type', 'application/json-rpc')

    result = urllib2.urlopen(req)
    result_str = result.read().decode('utf-8')
    result_json = json.loads(result_str)

    result_str = json.dumps(result_json, indent=4, separators=(',', ': '))

    funcend = timeit.default_timer()
    logger.info("Request to ZABBIX for method %s completed in %s seconds" %\
                (method, str(funcend - funcstart)))

    logger.debug("Response for method %s:\n%s" % (method, result_str))

    if "result" in result_json:
        return result_json["result"]
    elif "error" in result_json:
        logger.error(json.dumps(result_json["error"],
                                indent=4, separators=(',', ': ')
                                )
                     )
        return result_json
    else:
        return None
#===============================================================================