#!/bin/bash -ex
#python scripts/mod_config.py -c config -o addhost -h "vm-paramp-001" -v "range:9010-9020"
#python scripts/mod_config.py -c config -o addapp -a user -v "url:/Services/rest/company" -v "url:/Services/rest/user" -v "image:cmad_user_service" -v "imageport:8095" -v "version:latest"

#python scripts/mod_config.py -c config -o addapp -a web -v "defaulturl:true" -v "imageport:8095" -v "image:cmad_web_service" -v "version:latest"

#python scripts/mod_config.py -c config -o addapp -a blog -v "url:/Services/rest/blogs" -v "imageport:8095" -v "image:cmad_blog_service" -v "version:latest"

#python scripts/mod_config.py -c config -o addapp -a comment -v "url:/Services/rest/comment" -v "imageport:8095" -v "image:cmad_comment_service" -v "version:latest"

#python scripts/mod_config.py -c config -o starthaproxy -h "vm-paramp-001"
#python scripts/mod_config.py -c config -o stophaproxy -h "vm-paramp-001"
# add server
python scripts/mod_config.py -c config -o addserver -a user -v "version:latest"
#python scripts/mod_config.py -c config -o rmserver -a user -h vm-paramp-001:9019
