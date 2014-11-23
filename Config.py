__author__ = 'Sean Paley'
import os
from locale import *
import logging


setlocale(LC_NUMERIC, '')


class Config(object):
    #DW connection
    deployment = os.getenv('TRANSITION_DEPLOYMENT', 'LOCAL')
    print "TRANSITION_DEPLOYMENT: %s" % deployment
    LOCAL = deployment.lower() == "local"
    DATABASE_URI_LOCAL = "dbname=transition host=localhost user=python password=python"
    DATABASE_URI_SERVER = "dbname=igniteanalytics host=wsanalyticsdb.cmjbyzpmmqct.us-east-1.rds.amazonaws.com user= password="
    DATABASE_URI = DATABASE_URI_LOCAL if LOCAL else DATABASE_URI_SERVER
    DEBUG = True if LOCAL else False

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.INFO)