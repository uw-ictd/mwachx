#!/usr/bin/env bash

usage() {
cat <<EOF
usage: $0 options

Delete and recreate the database

Options
-h Show this message
EOF
options
}

options() {
cat <<EOF
-n Number of participants to make (default=10)
EOF
}

COUNT=10

while getopts "hn:" OPTION
do
    case $OPTION in
    h)
        usage
        exit 1
    ;;
    n)
        COUNT=$OPTARG
    ;;
	?)
		echo "Unkown Option: $OPTARG"
		usage
		exit 1
		;;
    esac
done

# Remove Old Sqlite File
rm mwach/mwach.db

# Migrate and Syncdb
python manage.py migrate --run-syncdb

python manage.py reset_db -n $COUNT
