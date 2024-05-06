#!/bin/bash
echo 'Running our UPS project...'

echo 'Attempting to make migrations...'
python3 manage.py makemigrations

echo 'Applying migrations...'
python3 manage.py migrate

while true
do
    python3 manage.py runserver 0.0.0.0:8080
    sleep 1
done