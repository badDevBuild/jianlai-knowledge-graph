#!/bin/bash
ssh -i insure.pem -o StrictHostKeyChecking=no root@shushu.host "ls -la /var/www/jianlai/data/ | head -n 5"
