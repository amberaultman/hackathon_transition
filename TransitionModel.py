__author__ = 'Sean Paley'
from lib.PGReader import PGReader, fetchone, fetchall, retrieve
from TransitionWriter import TransitionWriter
from pprint import pprint
from datetime import datetime
import logging
import json
from resources import *

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
            return writer.insert(table="tr_user", insert_dict=user_dict, get_serial=True)

    def update_user(self, user_dict):
        with TransitionWriter() as writer:
            user_dict["updated"] = datetime.utcnow()
            writer.update(table="tr_user", update_dict=user_dict)

    def delete_user(self, user_number):
        with TransitionWriter() as writer:
            writer.delete(table="tr_user", id_value=user_number, id_column="user_number")

    def stop_number(self, user_number):
        with TransitionWriter() as writer:
            writer.execute("UPDATE tr_user SET status = %(status) WHERE user_number = %(user_number)s; " \
                           + "UPDATE tr_user SET loved_number = null WHERE loved_number = %(user_number)s",
                params={"status": Statuses.STOP, "user_number": user_number})

    def is_loved_one(self, user_number, loved_number):
        return fetchone(self.database_uri, "SELECT 1 FROM tr_user WHERE user_number = %(user_number)s and loved_number = %(loved_number)s",
                 params={"user_number": user_number, "loved_number": loved_number}) is not None

    def user_numbers_for_loved_one(self, loved_number):
        results = fetchall(self.database_uri, "SELECT user_number FROM tr_user WHERE loved_number = %(loved_number)s",
                 params={"loved_number": loved_number})
        return [x["user_number"] for x in results]

    def is_valid_for_job(self, user_number):
        user_dict = self.retrieve_user(user_number)
        if not user_dict:
            return False, "User not found"

        if user_dict["status"] != Statuses.COMPLETE:
            return False, "User in incorrect status: %s" % user_dict["status"]

        return True, None

def log_message(user_number, message, response, success):
    message_dict = TransitionWriter.create_row("tr_message")
    with TransitionWriter() as writer:
        message_dict["created"] = datetime.utcnow()
        message_dict["user_number"] = user_number
        message_dump = {}
        for (key, val) in message.iteritems():
            message_dump[key] = val

        message_dict["message_json"] = json.dumps(message_dump)
        message_dict["response"] = response
        message_dict["success"] = success
        return writer.insert(table="tr_message", insert_dict=message_dict, get_serial=True)


class ContentModel(object):
    def __init__(self):
        self.database_uri = Config.DATABASE_URI

    def retrieve_content_url(self, user_number, content_type):
        content = retrieve(self.database_uri,
                        """SELECT * FROM tr_content
                           WHERE user_number = %(user_number)s
                            AND content_type = %(content_type)s
                            ORDER BY tr_content_nk DESC
                            LIMIT 1""",
                 params={"user_number": user_number, "content_type": content_type})

        return content["content_url"] if content else None

    def get_warning_content_urls(self, user_number):
        content = fetchall(self.database_uri,
                        """SELECT content_url FROM tr_content
                           WHERE user_number = %(user_number)s
                            AND content_type in (%(my)s, %(loved)s)
                            ORDER BY tr_content_nk DESC""",
                 params={"user_number": user_number, "my": ContentType.MY_WARNING, "loved": ContentType.LOVED_WARNING})

        return [x["content_url"] for x in content]

    def create_content(self):
        content_dict = TransitionWriter.create_row("tr_content")
        return content_dict

    def insert_content(self, content_dict):
        with TransitionWriter() as writer:
            content_dict["updated"] = content_dict["created"] = datetime.utcnow()
            writer.insert(table="tr_content", insert_dict=content_dict)

    def clear_pending(self, user_number):
        with TransitionWriter() as writer:
            writer.execute("UPDATE tr_content SET content_type = %(content_type)s WHERE user_number = %(user_number)s " \
                           + "AND content_type = %(pending)s",
                params={"content_type": ContentType.INACTIVE, "user_number": user_number, "pending": ContentType.PENDING})

    def clear_pending_loved(self, user_number):
        with TransitionWriter() as writer:
            writer.execute("UPDATE tr_content SET content_type = %(content_type)s WHERE user_number = %(user_number)s " \
                           + "AND content_type = %(pending)s",
                params={"content_type": ContentType.INACTIVE, "user_number": user_number, "pending": ContentType.PENDING_LOVED})

    def activate_pending_as_my_warning(self, user_number):
        with TransitionWriter() as writer:
            writer.execute("UPDATE tr_content SET content_type = %(content_type)s WHERE user_number = %(user_number)s " \
                           + "AND content_type = %(pending)s",
                params={"content_type": ContentType.MY_WARNING, "user_number": user_number, "pending": ContentType.PENDING})

    def activate_pending_as_loved_warning(self, user_number, new_number):
        with TransitionWriter() as writer:
            return writer.execute("UPDATE tr_content SET content_type = %(content_type)s, user_number = %(new_number)s " \
                            + "WHERE user_number = %(user_number)s AND content_type = %(pending)s",
                           params={"content_type": ContentType.LOVED_WARNING, "new_number": new_number, "user_number": user_number, "pending": ContentType.PENDING})

    def activate_pending_loved_as_loved_warning(self, user_number, new_number):
        with TransitionWriter() as writer:
            return writer.execute("UPDATE tr_content SET content_type = %(inactive)s " \
                            + "WHERE user_number = %(new_number)s AND content_type = %(loved)s;" \
                            + "UPDATE tr_content SET content_type = %(content_type)s, user_number = %(new_number)s " \
                            + "WHERE user_number = %(user_number)s AND content_type = %(pending)s",
                params={"content_type": ContentType.LOVED_WARNING, "new_number": new_number,
                        "user_number": user_number, "pending": ContentType.PENDING_LOVED,
                        "inactive": ContentType.INACTIVE, "loved": ContentType.LOVED_WARNING})

    def have_pending_loved(self, user_number):
        return fetchone(self.database_uri, "SELECT 1 FROM tr_content WHERE user_number = %(user_number)s and content_type = %(content_type)s",
                        params={"user_number": user_number, "content_type": ContentType.PENDING_LOVED}) is not None

    def deactivate_loved_warning(self, user_number):
        with TransitionWriter() as writer:
            writer.execute("UPDATE tr_content SET content_type = %(content_type)s " \
                            + "WHERE user_number = %(user_number)s AND content_type = %(loved)s",
                params={"content_type": ContentType.INACTIVE, "user_number": user_number, "loved": ContentType.LOVED_WARNING})

if __name__ == "__main__":
    user_model = UserModel()

    # test_number = "+19045551212"
    #
    # print user_model.retrieve_user(test_number)
    #
    # user = user_model.create_user()
    # user["user_number"] = test_number
    #
    # print user_model.insert_user(user)
    #
    # print user_model.retrieve_user(test_number)
    #
    # user_model.delete_user(test_number)
    #
    # print user_model.retrieve_user(test_number)

    print user_model.is_loved_one("+19045143943", "+19044770197")

    print user_model.user_numbers_for_loved_one("+19044770197")
    #log_message(1, {"test_message": "yo"})