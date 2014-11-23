__author__ = 'Sean Paley'


class Messages(object):
    INITIAL = "Welcome to kido, the app that helps you transition from work to home!  To register, please reply with the word 'register'"
    REGISTER = "Thanks for registering!  What's your name?"
    NAME = "Hi %(user_name)s - what time do you normally leave work?  Respond with a time like '5 PM' or '5:30 PM'."
    BAD_TIME = "Sorry, I didn't understand that.  Please respond with a time like '5 PM'."
    TIME = "Perfect. Kido works best when a loved one can send you a personal message for you when it's time to leave. " \
           + "Please provide their phone number like '123-456-7890' or enter 'skip'."
    BAD_PHONE = "Sorry, I didn't understand that.  Please respond with a phone number like '123-456-7890'."
    COMPLETE = "Ok, great, you're registered!  We look forward to helping you find work life balance!  If you need help at any time, simply message us. "
    MEDIA = "Thanks for that file. If you'd like to use this as your go home message please reply with 'me', else if it " \
            + "is for a loved one, please reply with their phone number like '123-456-7890'"
    MEDIA_ME_CONFIRM = "Awesome.  Your go home message is now set."
    MEDIA_LOVED_CONFIRM = "Your loved one's message is now set. Send another one at any time if you'd like to change it."
    MEDIA_NOT_LOVED = "Sorry, you are not set up as the loved one of that user. Please try again or enter 'skip' to cancel."
    MEDIA_SKIP = "OK, we'll skip that file."
    HELP = "Kido help - send a photo or video to use as a home reminder for yourself or a loved one. Text 'STOP' to cancel the Kido service. " \
                + "You are currently set to leave at %(leave_time)s. If you'd like to change that, respond with 'leave <time>' where time is like '5:30 PM'."
    STOP = "You are no longer registered with kido. Good-bye!"
    SINGLE_LOVED_MESSAGE = "Hi there! Your loved one with phone number %(user_number)s has started using a service called Kido. " \
           + "Kido helps people transition from work to home by sending them messages when it's time to go home. " \
            + "You can help! Please send a picture or video of someone expressing love for %(user_name)s.  Hint - kids work best..."
    MULTIPLE_LOVED_MESSAGE = "Hi there, popular one!  You've got multiple loved ones on the kido service.  Send a picture or video " \
            + "and then we'll ask who it's for."
    MULTIPLE_LOVED_MEDIA = "Thanks for that file. Please tell us which loved one this file is for. " \
            + "Please reply with their phone number like '123-456-7890'. Note, you must be specified as their loved one."
    #TODO: can ask loved one to register

    CALL_INITIAL_PROMPT = "Hi, this is kiddo with your daily download service. Hopefully you are on your way home now. " \
            + "This call will now record any thoughts you have and it will play them back to you in the morning.  " \
            + "Use this time to clear your head and leave yourself any todos for tomorrow." \
            + "Press any key when finished or hang up."
    CALL_THANKS = "Thank you and have a nice and meaningful night!"

    MORNING_MESSAGE = "Good morning, %(user_name)s.  We hope you had a great evening.  If you left yourself a message for today, play it above or below this text. " \
            + "You're currently expected to leave work at %(leave_time)s this evening.  If you'd like to change that, respond with 'leave <time>' where time is like '5:30 PM'."

    WARNING_MESSAGE = "Hi %(user_name)s.  We hope you had a great day!  It's time to pack up and head home.  Your loved ones miss you."

    HOME_CHANGED = "Your leave time has been changed to %(leave_time)s."

class Statuses(object):
    REGISTER = "register"
    NAME = "name"
    TIME = "time"
    COMPLETE = "complete"
    MEDIA = "media"
    STOP = "stop"


class ContentType(object):
    PENDING = "pending"
    INACTIVE = "inactive"
    MY_WARNING = "my_warning"
    LOVED_WARNING = "loved_warning"
    PENDING_LOVED = "pending_loved"
    MORNING = "morning"