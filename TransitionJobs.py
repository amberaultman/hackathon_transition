__author__ = 'Sean Paley'
from Config import Config
from twilio.rest import TwilioRestClient
from TransitionModel import *
from lib.lib import *

class TransitionJobs(object):
    def __init__(self):
        self.client = TwilioRestClient(Config.TWILIO_SID, Config.TWILIO_TOKEN)

    def make_drive_call(self, user_number):
        user_model = UserModel()
        valid = user_model.is_valid_for_job(user_number)
        if not valid[0]:
            return valid

        call = self.client.calls.create(to=user_number,
                                   from_=Config.TWILIO_FROM,
                                   url="",
                                   application_sid=Config.TWILIO_APP_SID)

        return True, "Drive call initiated. Twilio status: %s" % call.status


    def send_morning_text(self, user_number):
        content_model = ContentModel()
        user_model = UserModel()

        valid = user_model.is_valid_for_job(user_number)
        if not valid[0]:
            return valid

        user_dict = user_model.retrieve_user(user_number)

        user_dict["leave_time"] = format_leave_time(user_dict.get("leave_time")) if user_dict else None

        content_url = content_model.retrieve_content_url(user_number=user_number, content_type=ContentType.MORNING)

        sms = self.client.messages.create(body=Messages.MORNING_MESSAGE % user_dict,
                                          from_=Config.TWILIO_FROM,
                                          to=user_number,
                                          media_url=content_url)
        return True, "Morning text sent. Twilio status: %s" % sms.status

    def send_warning_text(self, user_number):
        content_model = ContentModel()
        user_model = UserModel()

        valid = user_model.is_valid_for_job(user_number)
        if not valid[0]:
            return valid

        user_dict = user_model.retrieve_user(user_number)

        warnings = content_model.get_warning_content_urls(user_number=user_number)
        # print warnings
        sms = self.client.messages.create(body=Messages.WARNING_MESSAGE % user_dict,
                                          from_=Config.TWILIO_FROM,
                                          to=user_number) #,
                                           #media_url=warnings)
        for content_url in warnings:
            self.client.messages.create(media_url=content_url,
                                          from_=Config.TWILIO_FROM,
                                          to=user_number)
        return True, "Warning text sent and %s content as well. Twilio status: %s" % (len(warnings), sms.status)


    def send_loved_prompt(self, user_number):
        content_model = ContentModel()
        user_model = UserModel()

        valid = user_model.is_valid_for_job(user_number)
        if not valid[0]:
            return valid

        user_dict = user_model.retrieve_user(user_number)

        loved_number = user_dict.get("loved_number")

        if not user_dict or not loved_number:
            return (False, "No loved number set.")

        if Config.DEBUG_LOVED:
            loved_number = Config.DEBUG_LOVED_NUMBER

        # print loved_number
        # loved_number = user_number

        sms = self.client.messages.create(body=Messages.SINGLE_LOVED_MESSAGE % user_dict,
                                          from_=Config.TWILIO_FROM,
                                          to=loved_number)
        return True, "Loved one prompt sent to %s. Twilio status: %s" \
               % ("test number" if Config.DEBUG_LOVED else loved_number, sms.status)


if __name__ == "__main__":
    jobs = TransitionJobs()
    #jobs.make_drive_call("+19045143943")
    jobs.send_morning_text("+19045143943")
    #jobs.send_warning_text("+19045143943")
    #jobs.send_loved_prompt("+19045143943")