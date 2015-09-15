Overview
========

Pipe-server for Maprox Observer project.
Listen for incoming packets from devices.

Supported protocols:

* Globalsat (TR-600, TR-203, TR-206, TR-151, TR-151 SP, GTR-128/GTR-129)
* Galileo
* Naviset (GT-10, GT-20)
* Teltonika FMXXXX (FM1100, FM3200, FM4200, FM5300), GH3000
* ATrack (AX5)
* Autolink
* GlobusGPS (TR1-mini)

Installation
============

Install git
-----------

    sudo apt-get update
    sudo apt-get install git

Install pip for python 3
------------------------

    sudo apt-get install python3-pip

Clone repository
----------------

    git clone https://github.com/maprox/Pipe.git
    cd Pipe

Install requirements
--------------------

    pip3 install -r requirements.txt --upgrade

Install redis
-------------
We can additionally install redis-server to this instance if we don't have
external server for it.

    sudo apt-get install redis-server

