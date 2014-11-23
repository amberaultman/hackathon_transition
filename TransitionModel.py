__author__ = 'Sean Paley'
from lib.PGReader import PGReader, fetchone, retrieve
from TransitionWriter import TransitionWriter
from pprint import pprint
from datetime import datetime
import logging
import json

from Config import Config


class UserModel(object):
    def __init__(self):
        self.database_uri = Config.DATABASE_URI

    def retrieve_user(self, user_number):
        return retrieve(self.database_uri, "SELECT * FROM tr_user WHERE user_number = %(user_number)s",
                 params={"user_number": user_number})

    def create_user(self):
        user_dict = TransitionWriter.create_row("tr_user")
        return user_dict

    def insert_user(self, user_dict):
        with TransitionWriter() as writer:
            user_dict["updated"] = user_dict["created"] = datetime.utcnow()
            writer.insert(table="tr_user", insert_dict=user_dict)

    def update_user(self, user_dict):
        with TransitionWriter() as writer:
            user_dict["updated"] = datetime.utcnow()
            writer.update(table="tr_user", update_dict=user_dict)

    def delete_user(self, user_number):
        with TransitionWriter() as writer:
            writer.delete(table="tr_user", id_value=user_number, id_column="user_number")

def log_message(tr_user_nk, message):
    message_dict = TransitionWriter.create_row("tr_message")
    with TransitionWriter() as writer:
        message_dict["created"] = datetime.utcnow()
        message_dict["message_json"] = json.dumps(message)
        writer.insert(table="tr_message", insert_dict=message_dict)


if __name__ == "__main__":
    user_model = UserModel()

    test_number = "+19045143943"

    print user_model.retrieve_user(test_number)

    user = user_model.create_user()
    user["user_number"] = test_number

    print user_model.insert_user(user)

    print user_model.retrieve_user(test_number)

    user_model.delete_user(test_number)

    print user_model.retrieve_user(test_number)


    log_message(1, {"test_message": "yo"})