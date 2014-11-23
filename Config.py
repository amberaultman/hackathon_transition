__author__ = 'Sean Paley'
import os
from locale import *
import logging


setlocale(LC_NUMERIC, '')


class Config(object):
    #DW connection
    deployment = os.getenv('TRANSITION_DEPLOYMENT', 'LOCAL')
    logging.getLogger().info("TRANSITION_DEPLOYMENT: %s" % deployment)
    LOCAL = deployment.lower() == "local"
    DATABASE_URI_LOCAL = "dbname=transition host=localhost user=python password=python"
    DATABASE_URI_SERVER = "dbname=igniteanalytics host=wsanalyticsdb.cmjbyzpmmqct.us-east-1.rds.amazonaws.com user= password="
    DATABASE_URI = DATABASE_URI_LOCAL if LOCAL else DATABASE_URI_SERVER
    DEBUG = True if LOCAL else False

    TWILIO_SID = 'ACcce45ceac814dcfc1a670d970e4bb981'
    TWILIO_TOKEN = '8e3515287d21d45b952e8b030bd8ed35'
    TWILIO_FROM = '+12015234663'
    TWILIO_APP_SID = 'APb1990ed299003d7e5091be5a61ee4eba'
    TWILIO_SESSION_SECRET = '\xec\xdd\xcb\xf0\x8c\xd8\xc8\x14\xb2\xff@\x0c\xd8\x84\x9db\x84\x05=A\x81 \x96\xaf'


    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.INFO)