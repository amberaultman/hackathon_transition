__author__ = 'Sean Paley'
from Config import Config
from twilio.rest import TwilioRestClient
from TransitionModel import *

class TransitionJobs(object):
    def __init__(self):
        self.client = TwilioRestClient(Config.TWILIO_SID, Config.TWILIO_TOKEN)

    def make_drive_call(self, user_number):
        # Make the call
        call = self.client.calls.create(to=user_number,
                                   from_=Config.TWILIO_FROM,
                                   url="",
                                   application_sid=Config.TWILIO_APP_SID)

        #print call.sid

    def send_morning_text(self, user_number):
        content_model = ContentModel()
        user_model = UserModel()

        user_db = user_model.retrieve_user(user_number)
        user_dict = {}
        user_dict.update(user_db)

        leave_time = user_dict["leave_time"] if user_dict and user_dict.get("leave_time") else None
        user_dict["leave_time"] = leave_time.strftime("%I:%M %p") if leave_time else None
        user_dict["content_url"] = content_model.retrieve_content_url(user_number=user_number, content_type=ContentType.MORNING)

        sms = self.client.messages.create(body=Messages.MORNING_MESSAGE % user_dict,
                                          from_=Config.TWILIO_FROM,
                                          to=user_number)


    def send_warning_text(self, user_number):
        content_model = ContentModel()
        user_model = UserModel()

        user_dict = user_model.retrieve_user(user_number)

        warnings = content_model.get_warning_content_urls(user_number=user_number)

        sms = self.client.messages.create(body=Messages.WARNING_MESSAGE % user_dict,
                                          from_=Config.TWILIO_FROM,
                                          to=user_number)
        for content_url in warnings:
            self.client.messages.create(media_url=content_url,
                                          from_=Config.TWILIO_FROM,
                                          to=user_number)


    def send_loved_prompt(self, user_number):
        content_model = ContentModel()
        user_model = UserModel()

        user_dict = user_model.retrieve_user(user_number)

        loved_number = user_dict.get("loved_number")

        if not user_dict or not loved_number:
            return

        # print loved_number
        # loved_number = user_number

        sms = self.client.messages.create(body=Messages.SINGLE_LOVED_MESSAGE % user_dict,
                                          from_=Config.TWILIO_FROM,
                                          to=loved_number)

if __name__ == "__main__":
    jobs = TransitionJobs()
    #jobs.make_drive_call("+19045143943")
    jobs.send_morning_text("+19045143943")
    #jobs.send_warning_text("+19045143943")
    #jobs.send_loved_prompt("+19045143943")