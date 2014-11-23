__author__ = 'Sean Paley'
from flask import Flask, request, redirect, session
import twilio.twiml, re
from pprint import pprint
from TransitionModel import *
import sys
from resources import *

app = Flask(__name__)

@app.route("/", methods=['GET'])
def default():
    return "This is the root."

@app.route("/twilio_sms", methods=['GET', 'POST'])
def twilio_sms():

    tr_user_nk = -1
    message = request.values
    response = None
    success = False
    user_model = UserModel()
    content_model = ContentModel()

    try:
        body = request.values.get("Body", None)
        body = body.strip() if body else None

        media_count = int(request.values.get("NumMedia", 0))
        media_urls = []
        for i in range(media_count):
            url = request.values.get("MediaUrl%s" % i)
            if url:
                media_urls.append(url)

        user_number = request.values["From"]
        user_dict = user_model.retrieve_user(user_number)
        if user_dict:
            tr_user_nk = user_dict["tr_user_nk"]

        status = user_dict["status"] if user_dict else None

        if body and body.lower() == 'stop':
            #note this won't do anything because twilio captures it
            user_model.stop_number(user_number)
            response = Messages.STOP

        elif not status or status == Statuses.STOP:
            user_dict = user_model.create_user()
            if body and re.match("register", body, flags=re.IGNORECASE):
                response = Messages.REGISTER
                user_dict["user_number"] = user_number
                user_dict["status"] = Statuses.REGISTER
                tr_user_nk = user_model.insert_user(user_dict)
            else:
                loved_users = user_model.user_numbers_for_loved_one(user_number)
                if not loved_users or len(loved_users) == 0:
                    response = Messages.INITIAL
                elif len(loved_users) == 1:
                    user_dict = user_model.retrieve_user(loved_users[0])
                    if media_count <= 0:
                        response = Messages.SINGLE_LOVED_MESSAGE
                    else:
                        response = Messages.MEDIA_LOVED_CONFIRM
                        content_dict = content_model.create_content()
                        content_dict["user_number"] = user_dict["user_number"]
                        content_dict["content_type"] = ContentType.LOVED_WARNING
                        content_dict["content_url"] = media_urls[0]
                        content_model.deactivate_loved_warning(user_dict["user_number"])
                        content_model.insert_content(content_dict)
                #multiple loved
                else:
                    if media_count <= 0:
                        response = Messages.MULTIPLE_LOVED_MESSAGE
                        pending_loved = content_model.have_pending_loved(user_number)

                        if pending_loved:
                            phn = parse_phone(body)
                            if phn:
                                user_dict = user_model.retrieve_user(phn)
                                if user_dict and user_dict["loved_number"] == user_number:
                                    count = content_model.activate_pending_loved_as_loved_warning(user_number, phn)
                                    if count:
                                        response = Messages.MEDIA_LOVED_CONFIRM
                                    else:
                                        response = Messages.MEDIA_NOT_LOVED
                                else:
                                    response = Messages.MEDIA_NOT_LOVED
                            elif body and body.lower() == "skip":
                                content_model.clear_pending_loved(user_number)
                            else:
                                response = Messages.MULTIPLE_LOVED_MEDIA
                    else:
                        response = Messages.MULTIPLE_LOVED_MEDIA
                        content_dict = content_model.create_content()
                        content_dict["user_number"] = user_number
                        content_dict["content_type"] = ContentType.PENDING_LOVED
                        content_dict["content_url"] = media_urls[0]
                        content_model.clear_pending_loved(user_number)
                        content_model.insert_content(content_dict)

        elif status == Statuses.REGISTER:
            if body:
                response = Messages.NAME
                user_dict["user_name"] = body
                user_dict["status"] = Statuses.NAME
                user_model.update_user(user_dict)
            else:
                response = Messages.REGISTER
        elif status == Statuses.NAME:
            dt = parse_time(body)
            if dt:
                response = Messages.TIME
                user_dict["leave_time"] = dt
                user_dict["status"] = Statuses.TIME
                user_model.update_user(user_dict)
            elif body:
                response = Messages.BAD_TIME
            else:
                response = Messages.NAME
        elif status == Statuses.TIME:
            phn = parse_phone(body)
            if phn or (body and body.lower() == "skip"):
                response = Messages.COMPLETE
                user_dict["loved_number"] = phn
                user_dict["status"] = Statuses.COMPLETE
                user_model.update_user(user_dict)
            elif body:
                response = Messages.BAD_PHONE
            else:
                response = Messages.TIME
        elif status == Statuses.COMPLETE:
            if len(media_urls) > 0:
                response = Messages.MEDIA
                user_dict["status"] = Statuses.MEDIA
                user_model.update_user(user_dict)

                content_dict = content_model.create_content()
                content_dict["user_number"] = user_number
                content_dict["content_type"] = ContentType.PENDING
                content_dict["content_url"] = media_urls[0]
                content_model.clear_pending(user_number)
                content_model.insert_content(content_dict)

            elif body:
                body = body.lower()
                response = Messages.HELP
        elif status == Statuses.MEDIA:
            phn = parse_phone(body)
            if body and body.lower() == 'me':
                response = Messages.MEDIA_ME_CONFIRM
                user_dict["status"] = Statuses.COMPLETE
                user_model.update_user(user_dict)

                content_model.activate_pending_as_my_warning(user_number)
            elif phn:
                if user_model.is_loved_one(phn, user_number):
                    response = Messages.MEDIA_LOVED_CONFIRM
                    user_dict["status"] = Statuses.COMPLETE
                    user_model.update_user(user_dict)
                    content_model.activate_pending_as_loved_warning(user_number, phn)
                else:
                    response = Messages.MEDIA_NOT_LOVED
            elif body and body.lower() == 'skip':
                response = Messages.MEDIA_SKIP
                user_dict["status"] = Statuses.COMPLETE
                user_model.update_user(user_dict)
                content_model.clear_pending(user_number)
            else:
                response = Messages.MEDIA


        else:
            response = "Sorry, something went wrong"


        resp = twilio.twiml.Response()
        resp.message(response % user_dict if user_dict else response)

        success = True

        return str(resp)

    except:
        response = sys.exc_info()[1].message
        raise
    finally:
        log_message(tr_user_nk=tr_user_nk, message=message, response=response, success=success)


def parse_time(time_input):
    if not time_input:
        return None
    m = re.search("""(?P<hour>[0,1]?\d):?(?P<minute>\d{1,2})?\s*(?P<ampm>am|pm)?""", time_input, re.IGNORECASE)
    if m:
        hour = int(m.group("hour"))
        minute = m.group("minute")
        if not minute:
            minute = 0
        ampm = m.group("ampm")
        ampm = ampm.lower() if ampm else "pm"
        if ampm == "pm":
            hour += 12

        return datetime(2000, 1, 1, hour, int(minute))
    return None

def parse_phone(phone_input):
    if not phone_input:
        return None
    m = re.search("""^\D*1?(\d{3})\D*(\d{3})\D*(\d{4})\D*$""", phone_input)
    if m:
        return "+1%s%s%s" % (m.group(1), m.group(2), m.group(3))
    return None

if __name__ == "__main__":
    app.run(debug=True)
    # print parse_phone("9045143943")
