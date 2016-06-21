# docker-orch
Python scripts to orchestrate microservices in docker.

Take a look at test/test_deploy.sh

You need to have passwordless ssh access to the server on which the containers will run.

python scripts/mod_config.py -c <config directory> -o \[ addhost | rmhost | addapp| rmapp| addserver| rmserver| starthaproxy | stophaproxy\] (other parameters)
config directory should have one file in the beginning (global, which is the common part of the haproxy config)
When you add or remove a server all haproxies are reloaded.

Right now it assumes only one haproxy in the setup.
