__author__ = 'Sean Paley'
from Config import Config
from lib.PGWriter import PGWriter
import logging

class TransitionWriter(PGWriter):
    def __init__(self):
        PGWriter.__init__(self, dsn=Config.DATABASE_URI)

    tables = [
        {
            "name": "tr_user",
            "primary_key": "tr_user_nk",
            "columns": [
                ('tr_user_nk', 'bigserial'),
                ('user_number', 'text'),
                ('user_name', 'text'),
                ('status', 'text'),
                ('leave_time', 'timestamp'),
                ('warn_time', 'timestamp'),
                ('transition_time', 'timestamp'),
                ('morning_time', 'timestamp'),
                ('loved_number', 'text'),
                ('created', 'timestamp'),
                ('updated', 'timestamp')
            ]
        },
        {
            "name": "tr_message",
            "primary_key": "tr_message_nk",
            "columns": [
                ('tr_message_nk', 'bigserial'),
                ('tr_user_nk', 'int8'),
                ('message_json', 'json'),
                ('created', 'timestamp')
            ]
        },
        {
            "name": "tr_content",
            "primary_key": "tr_content_nk",
            "columns": [
                ('tr_content_nk', 'bigserial'),
                ('tr_user_nk', 'int8'),
                ('tr_message_nk', 'int8'),
                ('content_type', 'text'),
                ('content_url', 'text'),
                ('created', 'timestamp')
            ]
        }
    ]

    files = [
        #"SDCDash1_Target.sql"
    ]

    def get_table_dicts(self):
        return self.tables

    def get_files(self):
        return __file__, self.files

    @staticmethod
    def create_row(table):
        for table_dict in TransitionWriter.tables:
            if table_dict["name"] == table:
                row_dict = {}
                for col in table_dict["columns"]:
                    row_dict[col[0]] = None
                return row_dict
        raise StandardError("Unknown table %s" % table)


if __name__ == '__main__':
    with TransitionWriter() as w:
        w.deploy()
