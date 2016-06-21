import getopt,sys
import shutil
import json
import os

def usage():
  print "make_config.py -c <config dir> -o <output dir> -p <port number to listen on>"

def clean_output(output_dir):
  try:
    shutil.rmtree(output_dir)  
  except:
    pass
  try:
    os.mkdir(output_dir)  
  except OSError,e:
    print(e.strerror)
    return 1
  return 0

def add_global(config_dir, output_dir):
  globalfp = open(config_dir+"/global",'r')
  outputfp = open(output_dir+"/haproxy.cfg",'w')
  outputfp.write(globalfp.read())
  outputfp.write("") 
  return outputfp

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
  
def add_servers(outputfp, app, cfg):
  host = 1
  for server in cfg["servers"]:
    outputfp.write("  server host"+str(host)+" "+server["host"]+"\n")
    host = host + 1

def compute_acl(app,obj):
  rules = []
  idx = 0
  if "acl" in obj:
    if type(obj["acl"]) is str or type(obj["acl"]) is unicode:
      rules.append("  acl "+app+str(idx)+" "+obj["acl"]+"\n") 
      idx+=1
    else:
      for acl in obj["acl"]:
        rules.append("  acl "+app+str(idx)+" "+acl+"\n")
        idx += 1
  if "url" in obj:
    if type(obj["url"]) is str or type(obj["url"]) is unicode:
      rules.append("  acl "+app+str(idx)+" path_beg -i "+obj["url"]+"\n") 
      idx +=1
    else:
      for url in obj["url"]:
        rules.append("  acl "+app+str(idx)+" path_beg -i "+url+"\n")
        idx+=1
  return rules

def write_config(outputfp, config_dir, port):
  outputfp.write("frontend web\n")
  outputfp.write("  bind *:"+str(port)+"\n")
  apps = get_apps(config_dir)
  cfgs={}
  numrules={}
  for app in apps:
    obj = get_app_config(config_dir, app)
    cfgs[app]=obj
    if "defaulturl" in obj:
      if obj["defaulturl"] == "true":
        outputfp.write("default_backend srvs_"+app+"\n")
    rules = compute_acl(app,obj)
    for rule in rules:
      outputfp.write(rule)
    numrules[app] = len(rules)
  outputfp.write("\n") 

  for app in apps:
    for a in range(numrules[app]):
      outputfp.write("use_backend srvs_"+app+"   if "+app+str(a)+"\n")
  outputfp.write("\n") 

  for app in apps:
    outputfp.write("backend srvs_"+app+"\n")
    outputfp.write("  balance roundrobin\n")
    add_servers(outputfp, app, cfgs[app])
    outputfp.write("\n") 


def remove_trailing_slash(s):
  if s[len(s) - 1] == '/':
    return s[:len(s)-1]
  return s

def write_haproxy_config(config_dir, output_dir, port):
  outputfp = add_global(config_dir, output_dir)
  write_config(outputfp, config_dir, port)

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "c:o:p:", [])
  except getopt.GetoptError as err:
    print str(err)
    usage()
    sys.exit(2)

  # default values
  config_dir = "config/"
  output_dir = "output/"
  port= "9001"
  for o, a in opts:
    if o == "-c":
      config_dir = a
    elif o == "-o":
      output_dir = a
    elif o == "-p":
      port = a
    else:
      print ("Invalid argument")
      usage()
      sys.exit(2)

  config_dir = remove_trailing_slash(config_dir)
  output_dir = remove_trailing_slash(output_dir)

  if clean_output(output_dir) == 1:
    print "Output dir cant be removed"
    sys.exit(2)
  write_haproxy_config(config_dir, output_dir, port)

if __name__ == "__main__":
  main()
