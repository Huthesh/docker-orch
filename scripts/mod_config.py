import getopt,sys
import shutil
import json
import os

def usage():
  print "mod_config.py -c <config dir> -a <app> -o <addserver|addapp|rmserver|rmapp> -h <hostname> -v <optional keyvalues>"

def get_apps(config_dir):
  applist=[]
  for root, dirs, files in os.walk(config_dir,topdown=True):
    for name in dirs:
      applist.append(name)
  return applist
 
def get_app_config(config_dir, app):
  fp = open(config_dir+"/"+app+"/config",'r')
  d = fp.read()
  return json.loads(d)
  
def remove_trailing_slash(s):
  if s[len(s) - 1] == '/':
    return s[:len(s)-1]
  return s

def checkservers(config_dir, host):
  apps = get_apps(config_dir)
  for app in apps:
    cfg = get_app_config(config_dir, app)
    for server in cfg["servers"]:
      if server["host"] == host:
        return False
  return True

def write_config(config_dir, app, obj):
  fp = open(config_dir+"/"+app+"/config","w")
  fp.write(json.dumps(obj))
  fp.close()

def addserver(config_dir, app, host, cfg):
  obj = {}
  if not checkservers(config_dir, host):
    print("Server is already added")
    sys.exit(2)

  try:
    obj = get_app_config(config_dir, app)
  except OSError,e:
    print (e.strerror)
    sys.exit(2)

  version=""
  if "version" in cfg:
    version = cfg["version"] 

  obj["servers"].append({"host": host, "version":version})
  write_config(config_dir, app, obj)
  sys.exit(0)

def rmserver(config_dir, app, host, cfg):
  obj = {}
  try:
    obj = get_app_config(config_dir, app)
  except OSError,e:
    print (e.strerror)
    sys.exit(2)

  result = []
  for server in obj["servers"]:
    if server["host"] != host:
      result.append(server)
  obj["servers"] = result
  if len(obj["servers"]) == 0:
    print ("Cant remove last server from the app")
    sys.exit(2)
  write_config(config_dir, app, obj)
  sys.exit(0)

def rmapp(config_dir, app):
  try:
    shutil.rmtree(config_dir+"/"+app)
  except OSError,e:
    print (e.strerror)
    sys.exit(2)
  sys.exit(0)

def addapp(config_dir, app, host, cfg):
  apps = get_apps(config_dir)
  for eapp in apps:
    if eapp == app:
      print("App already exists")
      sys.exit(2)

  if "url" not in cfg:
    print ("You need to pass in a url for the app")
    sys.exit(2)

  if len(host) == 0:
    print ("You need to specify a host")
    sys.exit(2)

  version = ""
  if "version" in cfg:
    version = cfg["version"]
 
  if not checkservers(config_dir, host):
    print ("server has already been added")
    sys.exit(2)

  try:
    os.mkdir(config_dir+"/"+app)
    obj = {"url":cfg["url"], "servers":[]}
    obj["servers"].append({"host":host,"version": version})
    write_config(config_dir, app, obj)
  except OSError,e:
    print (e.strerror)
    sys.exit(2)
  sys.exit(0)

def listconfig(config_dir):
  fp = open(config_dir+ "/global","r")
  print("Global Config:")
  print(fp.read())
  for app in get_apps(config_dir):
    print("Cluster: "+app)
    cfg = get_app_config(config_dir, app)
    print("  URL: "+cfg["url"])
    print("  Servers:")
    for server in cfg["servers"]:
      version=""
      if "version" in server:
        version = server["version"]
      print("    " + server["host"]+", version: "+version)
    print("")

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "c:o:h:v:a:", [])
  except getopt.GetoptError as err:
    print str(err)
    usage()
    sys.exit(2)

  # default values
  config_dir = "config/"
  option = "none"
  port= "9001"
  host=""
  app=""
  cfg={}
  for o, a in opts:
    if o == "-c":
      config_dir = a
    elif o == "-o":
      option = a
    elif o == "-h":
      host = a
    elif o == "-v":
      kv = a.split(":")  
      cfg[kv[0]] = kv[1]
    elif o == "-a":
      app = a
    else:
      print ("Invalid argument")
      usage()
      sys.exit(2)

  config_dir = remove_trailing_slash(config_dir)

  if len(app) == 0 and option != "listconfig":
    print("app(-a) is mandatory\n")
    usage()
    sys.exit(2) 

  if option == "addserver" and len(host) == 0:
    print("host (-h) is mandatory\n")
    usage()
    sys.exit(2) 

  if option == "none":
    print("Please pass a proper option (-o) [addserver|rmserver|addapp|rmapp]")
    usage()
    sys.exit(2)

  if option == "addserver":
    addserver(config_dir, app, host, cfg)
  elif option == "rmserver":
    rmserver(config_dir, app, host, cfg)
  elif option == "addapp":
    addapp(config_dir, app, host, cfg)
  elif option == "rmapp":
    rmapp(config_dir, app)
  elif option == "listconfig":
    listconfig(config_dir)
  else:
    print("Unknown command:"+option) 
    sys.exit(2)

  # all done
  sys.exit(0)


if __name__ == "__main__":
  main()
