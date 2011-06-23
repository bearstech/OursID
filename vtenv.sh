#!/bin/bash
# This script bootstraps a virtualenv 
# environement for demos

# Our script will not works without virtualenv
if test ! -f /usr/bin/virtualenv
then
echo "This script needs virtualenv"
exit 1
fi

# Starts
echo " * Create virtualenv vtenv"
virtualenv vtenv

# On Debian lenny version, virtualenv does not include activate_this.py
if test ! -f vtenv/bin/activate_this.py
then
echo " * Update virtualenv"
# Dowload virtualenv.py and update vtenv
wget http://bitbucket.org/ianb/virtualenv/raw/4b660247ce56/virtualenv.py
chmod u+x virtualenv.py
./virtualenv.py vtenv
rm virtualenv.py
# Oh, and yes : its prety ugly.....
fi

# Start bootstrap
echo " * Enter Virtualenv"
source vtenv/bin/activate
echo " * Install pip"
easy_install pip
easy_install "setuptools>=0.6c9"
echo " * Pip install requirements"
pip -E vtenv install -r requirements.txt --upgrade
echo " * Leave Virtualenv"
deactivate

# Activate virtualenv compat on our project
echo " * Activate virtualenv on project"
sed -i "s/# activate_this =/activate_this =/g" OursID/manage.py OursID/deploy/deploy.wsgi
sed -i "s/# execfile/execfile/g" OursID/manage.py OursID/deploy/deploy.wsgi
echo " * Done"
exit
