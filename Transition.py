__author__ = 'Sean Paley'
from flask import Flask, request, redirect, session, flash, render_template
import twilio.twiml, re
from pprint import pprint
from TransitionModel import *
import sys
from resources import *
from lib.lib import *
from TransitionJobs import *

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/", methods=['GET'])
def default():
    return "This is the root."

@app.route("/twilio_sms", methods=['GET', 'POST'])
def twilio_sms():

    message = request.values
    response = None
    success = False
    user_model = UserModel()
    content_model = ContentModel()
    user_number = request.values["From"]

    try:
        body = request.values.get("Body", None)
        body = body.strip() if body else None

        media_count = int(request.values.get("NumMedia", 0))
        media_urls = []
        for i in range(media_count):
            url = request.values.get("MediaUrl%s" % i)
            if url:
                media_urls.append(url)

        user_dict = user_model.retrieve_user(user_number)

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
                user_model.insert_user(user_dict)
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
                if body.startswith("leave"):
                    dt = parse_time(body)
                    if dt:
                        response = Messages.HOME_CHANGED
                        user_dict["leave_time"] = dt
                        user_model.update_user(user_dict)
                    else:
                        response = Messages.BAD_TIME
                else:
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

        real_user_dict = {}
        if user_dict:
            real_user_dict.update(user_dict)
            real_user_dict["leave_time"] = format_leave_time(real_user_dict.get("leave_time"))

        resp = twilio.twiml.Response()
        resp.message(response % real_user_dict if real_user_dict else "")

        success = True

        return str(resp)

    except:
        response = sys.exc_info()[1].message
        raise
    finally:
        log_message(user_number=user_number, message=message, response=response, success=success)


@app.route("/twilio_phone", methods=['GET', 'POST'])
def twilio_phone():
    resp = twilio.twiml.Response()
    resp.say(Messages.CALL_INITIAL_PROMPT, voice="woman")
    resp.record(maxLength=300, action="/twilio_phone_thanks")
    return str(resp)

@app.route("/twilio_phone_thanks", methods=['GET', 'POST'])
def twilio_phone_complete():
    message = request.values
    response = None
    success = False
    user_model = UserModel()
    content_model = ContentModel()
    user_number = request.values.get("Called")

    try:
        body = request.values.get("Body", None)
        body = body.strip() if body else None

        recording_duration = int(request.values.get("RecordingDuration", 0))
        recording_url = request.values.get("RecordingUrl", None)

        if recording_url:
            if not recording_url.endswith(".mp3"):
                recording_url += ".mp3"
            recording_url = recording_url.replace("http://", "https://")

        content_dict = content_model.create_content()
        content_dict["user_number"] = user_number
        content_dict["content_type"] = ContentType.MORNING
        content_dict["content_url"] = recording_url
        content_model.insert_content(content_dict)

        resp = twilio.twiml.Response()
        resp.say(Messages.CALL_THANKS, voice="woman")

        success = True

        return str(resp)

    except:
        response = sys.exc_info()[1].message
        raise
    finally:
        log_message(user_number=user_number, message=message, response=response, success=success)

@app.route('/testjobs', methods=['GET', 'POST'])
def testjobs():
    error = None
    user_number = ""
    if request.method == 'POST':
        job = request.form.get("job")
        user_number = request.form.get("user_number", "").strip()
        result = None

        jobs = TransitionJobs()

        if not session.get("logged_in", False):
            if request.form.get("test_password") != Config.TEST_PASSWORD:
                error = "Incorrect test password"
            else:
                session["logged_in"] = True
        elif not user_number:
            error = "User number not specified"
        else:
            valid = UserModel().is_valid_for_job(user_number)
            if not valid[0]:
                error = valid[1]

        if not job:
            error = "No job specified"

        if not error:
            job_result = (False, "Unknown job")
            if job == "morning":
                job_result = jobs.send_morning_text(user_number)
            elif job=="warning":
                job_result = jobs.send_warning_text(user_number)
            elif job=="drive":
                job_result = jobs.make_drive_call(user_number)
            elif job=="loved":
                job_result = jobs.send_loved_prompt(user_number)

            if job_result[0]:
                result = job_result[1]
            else:
                error = job_result[1]

        if result:
            flash(result)
    return render_template('testjobs.html', error=error)


if __name__ == "__main__":
    app.run(debug=True)
    # print parse_phone("9045143943")
