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

def getfreehost(config_dir):
  fp = open(config_dir+"/host_config","r")
  gcfg = json.loads(fp.read())
  num = -1
  rethost = ""
  for host in gcfg:
    if num == -1:
      if len(gcfg[host]["ports_used"]) != len(gcfg[host]["ports"]):
        num = len(gcfg[host]["ports_used"]) 
        rethost = host
    elif len(gcfg[host]["ports_used"]) != len(gcfg[host]["ports"]):
      if len(gcfg[host]["ports"]) < num:
        num = len(gcfg[host]["ports"])
        rethost = host
  if len(rethost) == 0:
    print "Failed to find a free host!"
    sys.exit(2)
  return rethost
 
def addserver(config_dir, app, host, cfg):
  obj = {}
  if len(host) == 0:
    # need to select a host
    host = getfreehost(config_dir)

  if ":" not in host:
    port = getport(config_dir, host) 
    host = host + ":" + str(port)

  if not checkservers(config_dir, host):
    print("Server is already added")
    sys.exit(2)

  try:
    obj = get_app_config(config_dir, app)
  except OSError,e:
    print (e.strerror)
    sys.exit(2)

  obj = {"host": host}
  version=""
  if "version" in cfg:
    version = cfg["version"] 
  obj["version"] = version

  if "instance" in cfg:
    obj["instance"] = cfg["instance"]
  else:
    obj["instance"] = ""

  obj["servers"].append( "version":version})
  write_config(config_dir, app, obj)
  sys.exit(0)

def rmserver(config_dir, app, host, cfg):
  if ":" not in host:
    print ("I need the full server name hostname:port to remove")
    sys.exit(2)

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
  returnport(config_dir, host.split(":")[0], host.split(":")[1])
  sys.exit(0)

def listservers(config_dir, cfg):
  if "version" in cfg and "app" in cfg:
    appcfg = get_app_config(config_dir, app) 
    for server in appcfg["servers"]:
      if server["version"] == cfg["version"] 
        print(server["host"]+" "+server["version"]+" "+server["instance"])
    return
  
  if "app" in cfg:
    appcfg = get_app_config(config_dir, app) 
    for server in appcfg["servers"]:
      print(server["host"]+" "+server["version"]+" "+server["instance"])
    return

  if "host" in cfg:
    for appcfg in get_apps(config_dir):
      for server in appcfg["servers"]:
        if server["host"] == cfg["host"]:
          print(server["host"]+" "+server["version"]+" "+server["instance"])
    return
   
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

def gen_range(r):
  litems = []
  items = r.split(",")
  for item in items:
    if '-' not in item:
      litems.append(int(item))
    else:
      idx = item.split("-")
      for i in range(int(idx[0]), int(idx[1])):
        litems.append(i)
  return litems
      
def addhost(config_dir, host, port_range):
  fp = None
  try:
    fp = open(config_dir+"/host_config","r")
    gcfg = json.loads(fp.read())
  except:
    gcfg = {"hosts":{}} 
  l = gen_range(port_range)
  if host not in gcfg["hosts"]:
    gcfg["hosts"][host] = {"ports":l,"ports_used":[]} 
  else:
    #modification case
    gcfg["hosts"][host] = {"ports":l,"ports_used":[]} 
  if fp:
    fp.close()
  fp = open(config_dir+"/host_config","w")
  fp.write(json.dumps(gcfg))
  fp.close()

def rmhost(config_dir, host):
  fp = open(config_dir+"/host_config","r")
  gcfg = json.loads(fp.read())
  l = gen_range(port_range)
  if host in gcfg["hosts"]:
    del(gcfg["hosts"][host]) 
  fp.close()
  fp = open(config_dir+"/host_config","w")
  fp.write(json.dumps(gcfg))
  fp.close()

def chooseport(ports, ports_used):
  selected = -1
  for i in ports:
    if i not in ports_used:
      selected = i;
  return selected
 
def getport(config_dir, host):
  fp = open(config_dir+"/host_config","r")
  gcfg = json.loads(fp.read())
  ret = chooseport(gcfg[host]["ports"], gcfg[host]["ports_used"])
  if ret < 0:
    print ("No free ports in "+host)
    sys.exit(2)
  gcfg[host]["ports_used"].append(ret)  
  fp.close()
  fp = open(config_dir+"/host_config","w")
  fp.write(json.dumps(gcfg))
  fp.close()


  return ret

def returnport(config_dir, host, port):
  fp = open(config_dir+"/host_config","r")
  gcfg = json.loads(fp.read())
  gcfg[host]["ports_used"].remove(int(port))
  fp.close()
  fp = open(config_dir+"/host_config","w")
  fp.write(json.dumps(gcfg))
  fp.close()
 
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

  if option == "none":
    print("Please pass a proper option (-o) [addserver|rmserver|addapp|rmapp|listconfig]")
    usage()
    sys.exit(2)

  if len(app) == 0 and option != "listconfig":
    print("app(-a) is mandatory\n")
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
  elif option == "addhost":
    if "range" not in cfg:
      print("need to have a port range to add a host")
      sys.exit(2)
    addhost(config_dir, host, cfg["range"])
  elif option == "rmhost":
    rmhost(config_dir, host)
  elif option == "listservers":
    listservers(config_dir, cfg)
  else:
    print("Unknown command:"+option) 
    sys.exit(2)

  # all done
  sys.exit(0)


if __name__ == "__main__":
  main()
