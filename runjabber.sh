#!/usr/bin/env bash
env_path='/home/nyasha/env/'
settings="settings_prod"
cd ${env_path}
source bin/activate
cd nyasha
python manage.py runjabber --settings=${settings} $*
