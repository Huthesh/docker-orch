import sys,os
import subprocess
import time
#cmd is an array of cmd and args
def run_command(dest, cmd):
  try:
    output = subprocess.check_output(["ssh",dest]+cmd) 
    return output,0
  except  subprocess.CalledProcessError,ce:
    return ce.output,ce.returncode

def copy_file(dest, filename, output_file):
  try:
    output = subprocess.check_output(["scp", filename, dest+":"+output_file]) 
    return output,0
  except  subprocess.CalledProcessError,ce:
    return ce.output,ce.returncode


# port is a tuple [out,in] out is the port open outside and in is the port
# on the container.
# will return the container that was started or the error code
def run_container(dest, port, container, name):
  return run_command(dest,["docker","run", "--name",name,
    "-p", str(port[0])+":"+str(port[1]),
    "-d", # daemonize
    container])

def stop_container(dest, instance):
  output,rc = run_command(dest,["docker", "stop", instance])
  if rc == 0:
    return rm_container(dest, instance)
  return output,rc  

def rm_container(dest, instance):
  return run_command(dest,["docker", "rm", instance])

def restarthaproxy(host, cfg_filename, port, name):
  output,rc = copy_file(host, cfg_filename, "haproxy_build_"+str(port)+"/haproxy.cfg")
  if rc != 0:
    print "Failed to copy haproxy config"
    return output,rc
  output,rc = run_command(host, ["pwd"])
  return run_command(host, ["docker","kill","-s", "HUP", name])


def starthaproxy(host, cfg_filename, port, name):
  output,rc = run_command(host, ["rm","-rf","haproxy_build_"+str(port)])
  # ignore the error
  output,rc = run_command(host,["mkdir","-p", "haproxy_build_"+str(port)])
  if rc != 0:
    print "Failed to mkdir"
    return output,rc
  output,rc = copy_file(host, cfg_filename, "haproxy_build_"+str(port)+"/haproxy.cfg")
  if rc != 0:
    print "Failed to copy haproxy config"
    return output,rc
  output,rc = run_command(host, ["pwd"])
  return run_command(host, ["docker","run","-d",
    "--name",name,
    "-v",output.replace("\n","")+"/"+"haproxy_build_"+str(port)+"/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro",
    "-p",str(port)+":80","haproxy:latest"])

def stophaproxy(host, instance):
  output,rc = stop_container(host, instance)
  if rc != 0:
    return rm_container(host, instance)
  return output,rc
def main():
  output,rc = run_container("vm-paramp-001",[9010,8095],"cmad_user_service:latest","blabla")
  if rc == 0: 
    time.sleep(30)
    output,rc = stop_container("vm-paramp-001", "blabla")
    if rc == 0:
      print output
    else:
      print "failed to stop container:"+"blabla"
  else:
    print("Run Container failed")
    sys.exit

if __name__ == "__main__":
  main()
