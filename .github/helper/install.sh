#!/bin/bash
# Copied from https://github.com/frappe/press/blob/develop/.github/helper/install.sh

set -e

cd ~ || exit

sudo apt update && sudo apt install redis-server libcups2-dev

pip install frappe-bench
bench init --skip-assets --python "$(which python)" ~/frappe-bench

mysql --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mysql --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

cd ~/frappe-bench || exit

sed -i 's/watch:/# watch:/g' Procfile
sed -i 's/schedule:/# schedule:/g' Procfile
sed -i 's/socketio:/# socketio:/g' Procfile
sed -i 's/redis_socketio:/# redis_socketio:/g' Procfile

bench get-app otto "${GITHUB_WORKSPACE}"

bench setup requirements --dev

bench start &> bench_start_logs.txt &
CI=Yes bench build --app frappe &
bench new-site --db-root-password root --admin-password admin test_site
bench --site test_site install-app otto
bench set-config -g server_script_enabled 1
bench set-config -g http_port 8000