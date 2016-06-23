#!/bin/bash -ex
#python scripts/mod_config.py -c config -o addhost -h "vm-paramp-001" -v "range:9010-9020"
python scripts/mod_config.py -c config -o addapp -a user -v "url:/Services/rest/company" -v "url:/Services/rest/user" -v "image:paramp/cmad_user_service" -v "imageport:8095" -v "version:3.3"

#python scripts/mod_config.py -c config -o addapp -a web -v "defaulturl:true" -v "imageport:8095" -v "image:paramp/cmad_webjs_service" -v "version:3.7"

#python scripts/mod_config.py -c config -o addapp -a blog -v "url:/Services/rest/blogs" -v "imageport:8095" -v "image:paramp/cmad_blog_service" -v "version:4.0"

#python scripts/mod_config.py -c config -o addapp -a comment -v "url:/Services/rest/comment" -v "imageport:8095" -v "image:paramp/cmad_comment_service" -v "version:3.2"

#python scripts/mod_config.py -c config -o addapp -a chat -v "url:/eventbus" -v "imageport:8095" -v "image:paramp/cmad_chat_service" -v "version:3.3"

#python scripts/mod_config.py -c config -o starthaproxy -h "vm-paramp-001"
python scripts/mod_config.py -c config -o stophaproxy -h "vm-paramp-001"
python scripts/mod_config.py -c config -o starthaproxy -h "vm-paramp-001"
# add server
#python scripts/mod_config.py -c config -o addserver -a web -v "version:3.5"
#python scripts/mod_config.py -c config -o rmserver -a user -h vm-paramp-001:9019
