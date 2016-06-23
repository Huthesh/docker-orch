import getopt,sys
import shutil
import json
import os
import driver
from driver import run_container, stop_container
from make_config import write_haproxy_config
from tempfile import mkdtemp
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
  for host in gcfg["hosts"]:
    if num == -1:
      if len(gcfg["hosts"][host]["ports_used"]) != len(gcfg["hosts"][host]["ports"]):
        num = len(gcfg["hosts"][host]["ports_used"]) 
        rethost = host
    elif len(gcfg["hosts"][host]["ports_used"]) != len(gcfg["hosts"][host]["ports"]):
      if len(gcfg["hosts"][host]["ports"]) < num:
        num = len(gcfg["hosts"][host]["ports"])
        rethost = host
  if len(rethost) == 0:
    print "Failed to find a free host!"
    sys.exit(2)
  return rethost
 
def cfgserver(config_dir, app, host, cfg):
  obj = None
  try:
    obj = get_app_config(config_dir, app)
  except OSError,e:
    print (e.strerror)
    sys.exit(2)

  for server in obj["servers"]:
    if server["host"] == host:
      for k in cfg:
        server[k] = cfg[k] 
      break
  write_config(config_dir, app, obj)
  print host
  sys.exit(0)


def addserver(config_dir, app, host, cfg):
  obj = {}
  if len(host) == 0:
    # need to select a host
    host = getfreehost(config_dir)
  port = 0
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

  nobj = {"host": host}
  version=""
  fullversion=""
  if "version" in cfg:
    version = cfg["version"] 
    fullversion=":"+version
  nobj["version"] = version

  if "instance" in cfg:
    nobj["instance"] = cfg["instance"]
  else:
    nobj["instance"] = host.replace(":","_")
  output,rc = run_container(host.split(":")[0], [host.split(":")[1],obj["imageport"]],obj["image"]+fullversion,nobj["instance"])
  if rc != 0:
    print("Failed to start container")
    returnport(config_dir, host.split(":")[0], host.split(":")[1])
    sys.exit(2)
  obj["servers"].append(nobj)
  write_config(config_dir, app, obj)
  print host
  #FIXME this assumes haproxy is on 80
  restarthaproxy(config_dir)
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
  delserver = None
  for server in obj["servers"]:
    if server["host"] != host:
      result.append(server)
    else:
      delserver = server

  if len(result) == 0:
    print ("Cant remove last server from the app")
    sys.exit(2)

  obj["servers"] = result
  # now do the actual removal
  output,rc = stop_container(host.split(":")[0], delserver["instance"])
  if rc != 0:
    print ("Failed to stop container")
    sys.exit(2)
 
  write_config(config_dir, app, obj)
  returnport(config_dir, host.split(":")[0], host.split(":")[1])
  restarthaproxy(config_dir)
  sys.exit(0)

def listservers(config_dir, cfg):
  if "version" in cfg and "app" in cfg:
    appcfg = get_app_config(config_dir, cfg["app"]) 
    for server in appcfg["servers"]:
      if server["version"] == cfg["version"]:
        print(server["host"]+" "+server["version"]+" "+server["instance"])
    return
  
  if "app" in cfg:
    appcfg = get_app_config(config_dir, cfg["app"]) 
    for server in appcfg["servers"]:
      print(server["host"]+" "+server["version"]+" "+server["instance"])
    return

  if "host" in cfg:
    for appcfg in get_apps(config_dir):
      for server in appcfg["servers"]:
        if server["host"] == cfg["host"]:
          print(server["host"]+" "+server["version"]+" "+server["instance"])
    return
   
# FIXME need to deallocate ports
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

  if "url" not in cfg and "acl" not in cfg and "defaulturl" not in cfg:
    print ("You need to pass in atleast one url or acl or defaulturl for the app")
    sys.exit(2)

  if "image" not in cfg or "imageport" not in cfg:
    print("You need to pass the docker image basename and imageport")
    sys.exit(2)


  if "version" not in cfg:
    print("You need to pass the docker image version")
    sys.exit(2)

  if len(host) == 0:
    # need to select a host
    host = getfreehost(config_dir)
  port = ""
  if ":" not in host:
    port = getport(config_dir, host) 
    host = host + ":" + str(port)
  else:
    port = host.split(":")[1]

  version = ""
  if "version" in cfg:
    version = cfg["version"]
 
  instance = ""
  if "instance" in cfg:
    instance = cfg["instance"]
 
  if not checkservers(config_dir, host):
    print ("server has already been added")
    sys.exit(2)

  imagename = ""
  if len(version) == 0:
    imagename = cfg["image"]
  else:
    imagename = cfg["image"]+":"+version

  if len(instance) == 0:
    instance = host.replace(":","_")
  output,rc = run_container(host.split(":")[0], [port,cfg["imageport"]],imagename,instance)
  if rc != 0:
    print "Failed to Add App"
    returnport(config_dir, host.split(":")[0], host.split(":")[1])
    sys.exit(2)
  try:
    os.mkdir(config_dir+"/"+app)
    obj = {"image":cfg["image"],
           "imageport":cfg["imageport"],
           "servers":[]}
    if "url" in cfg:
      obj["url"] = cfg["url"]
    if "acl" in cfg:
      obj["acl"] = cfg["acl"]
    if "defaulturl" in cfg:
      obj["defaulturl"] = cfg["defaulturl"]
    obj["servers"].append({"host":host,"version": version, "instance": instance})
    write_config(config_dir, app, obj)
  except OSError,e:
    print (e.strerror)
    sys.exit(2)
  print host
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

#FIXME need to add a way to update the app entries as well
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
  ret = chooseport(gcfg["hosts"][host]["ports"], gcfg["hosts"][host]["ports_used"])
  if ret < 0:
    print ("No free ports in "+host)
    sys.exit(2)
  gcfg["hosts"][host]["ports_used"].append(ret)  
  fp.close()
  fp = open(config_dir+"/host_config","w")
  fp.write(json.dumps(gcfg))
  fp.close()
  return ret

def returnport(config_dir, host, port):
  fp = open(config_dir+"/host_config","r")
  gcfg = json.loads(fp.read())
  gcfg["hosts"][host]["ports_used"].remove(int(port))
  fp.close()
  fp = open(config_dir+"/host_config","w")
  fp.write(json.dumps(gcfg))
  fp.close()

def restarthaproxy(config_dir):
  fp = None
  try:
    fp = open(config_dir+"/haproxy_config","r")
    gcfg=json.loads(fp.read())
  except:
    gcfg=[]

  if fp:
    fp.close()

  output_dir = mkdtemp()
  # haproxy always listens on local 80, we will map it some other port on the 
  # host
  write_haproxy_config(config_dir, output_dir, 80) 
  # FIXME we restart each haproxy
  found = False
  ncfg = []
  failed = False
  for hap in gcfg:
    found = True
    ha_name = hap["host"]+"_"+str(hap["port"])
    output,rc = driver.restarthaproxy(hap["host"], output_dir+"/haproxy.cfg",hap["port"],ha_name)
    if rc != 0:
      failed = True
    else:
      ncfg.append(hap)
  shutil.rmtree(output_dir)

  if not found:
    print "Could not find haproxy"
    sys.exit(2)
  if not failed: 
    print "Success"
    sys.exit(0)
  else:
    # failed to restart to remove the haproxy from the config
    fp = open(config_dir+"/haproxy_config","w")
    fp.write(json.dumps(ncfg))
    print "Failed"
    sys.exit(2)


def starthaproxy(config_dir, host, cfg):
  # assumes haproxy has not been started yet
  fp = None
  try:
    fp = open(config_dir+"/haproxy_config","r")
    gcfg=json.loads(fp.read())
  except:
    gcfg=[]

  if fp:
    fp.close()

  hcfg = {}
  if "port" in cfg:
    hcfg["port"] = cfg["port"]
  else:
    hcfg["port"] = 80

  hcfg["host"] = host
  for hap in gcfg:
    if hap["port"] == hcfg["port"] and hap["host"] == hcfg["host"]:
      print "Ha Proxy is already started. stop it first!"
      sys.exit(2)
  output_dir = mkdtemp()
  # haproxy always listens on local 80, we will map it some other port on the 
  # host
  write_haproxy_config(config_dir, output_dir, 80) 
  ha_name = host+"_"+str(hcfg["port"])
  output,rc = driver.starthaproxy(host, output_dir+"/haproxy.cfg",hcfg["port"],ha_name)
  shutil.rmtree(output_dir)
  if rc == 0:
    hcfg["instance"] = ha_name
    gcfg.append(hcfg)
    fp = open(config_dir+"/haproxy_config","w")
    fp.write(json.dumps(gcfg))
    print "Success"
    sys.exit(0)
  else:
    print "Failed"
    sys.exit(2)

def stophaproxy(config_dir, host, cfg):
  # assumes haproxy has not been started yet
  fp = None
  try:
    fp = open(config_dir+"/haproxy_config","r")
    gcfg=json.loads(fp.read())
  except:
    print "Failed to find haproxy config"
    sys.exit(2)
  if fp:
    fp.close()
  hcfg = {}
  if "port" in cfg:
    hcfg["port"] = cfg["port"]
  else:
    hcfg["port"] = 80

  hcfg["host"] = host
  ncfg = []
  rc = -1
  for hap in gcfg:
    if hap["port"] == hcfg["port"] and hap["host"] == hcfg["host"]:
      output,rc = driver.stophaproxy(host, hap["instance"])
      if rc != 0:
        sys.exit(2)
    else:
      ncfg.append(hap)
  if rc == 0:
    fp = open(config_dir+"/haproxy_config","w")
    fp.write(json.dumps(ncfg))
    print "Success"
    sys.exit(0)
  sys.exit(2)
 
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
      if kv[0] in cfg:
        if type(cfg[kv[0]]) is str or type(cfg[kv[0]]) is unicode:
          cfg[kv[0]] = [cfg[kv[0]],kv[1]]
        else:
          cfg[kv[0]].append(kv[1])
      else:
        cfg[kv[0]] = kv[1]
    elif o == "-a":
      app = a
    else:
      print ("Invalid argument")
      usage()
      sys.exit(2)

  config_dir = remove_trailing_slash(config_dir)

  if option == "none":
    print("Please pass a proper option (-o) [addhost|rmhost|addserver|cfgserver|rmserver|addapp|rmapp|listconfig|listservers|starthaproxy|stophaproxy]")
    usage()
    sys.exit(2)

  if option == "addserver":
    if len(app) == 0:
      print("app(-a) is mandatory\n")
      usage()
      sys.exit(2) 
    addserver(config_dir, app, host, cfg)
  elif option == "cfgserver":
    if len(app) == 0:
      print("app(-a) is mandatory\n")
      usage()
      sys.exit(2) 

    cfgserver(config_dir, app, host, cfg)
  elif option == "rmserver":
    if len(app) == 0:
      print("app(-a) is mandatory\n")
      usage()
      sys.exit(2) 

    rmserver(config_dir, app, host, cfg)
  elif option == "addapp":
    if len(app) == 0:
      print("app(-a) is mandatory\n")
      usage()
      sys.exit(2) 

    addapp(config_dir, app, host, cfg)
  elif option == "rmapp":
    if len(app) == 0:
      print("app(-a) is mandatory\n")
      usage()
      sys.exit(2) 

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
  elif option == "starthaproxy":
    starthaproxy(config_dir, host, cfg)
  elif option == "stophaproxy":
    stophaproxy(config_dir, host, cfg)
  else:
    print("Unknown command:"+option) 
    sys.exit(2)

  # all done
  sys.exit(0)


if __name__ == "__main__":
  main()
