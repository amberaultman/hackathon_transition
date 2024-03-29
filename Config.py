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
    DATABASE_URI_SERVER = "postgres://gqhejsmyivbhox:rblfio9K3UveAACq1uucP6CMVb@ec2-54-197-249-212.compute-1.amazonaws.com:5432/ddo2h0see3cur3"
    DATABASE_URI = DATABASE_URI_LOCAL if LOCAL else DATABASE_URI_SERVER
    DEBUG = True if LOCAL else False
    SECRET_KEY = '\xec\xdd\xcb\xf0\x8c\xd8\xc8\x14\xb2\xff@\x0c\xd8\x84\x9db\x84\x05=A\x81 \x96\xaf'
    TEST_PASSWORD = 'driveis008'
    DEBUG_LOVED = True
    DEBUG_LOVED_NUMBER = "+19045143943"

    TWILIO_SID = 'ACcce45ceac814dcfc1a670d970e4bb981'
    TWILIO_TOKEN = '8e3515287d21d45b952e8b030bd8ed35'
    TWILIO_FROM = '+12015234663'
    TWILIO_APP_SID = 'APb1990ed299003d7e5091be5a61ee4eba'


    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG if DEBUG else logging.INFO)