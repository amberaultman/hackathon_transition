__author__ = 'Sean Paley'
from flask import Flask, request, redirect, session
import twilio.twiml, re
from pprint import pprint
from TransitionWriter import TransitionWriter

app = Flask(__name__)

@app.route("/", methods=['GET'])
def default():
    return "This is the root."

@app.route("/twilio", methods=['GET', 'POST'])
def twilio():
    """Respond to incoming calls with a simple text message."""
    step = session.get("step", 0)
    name = session.get("name")
    loved = session.get("loved")
    leave = session.get("leave")

    body = request.values.get("Body", "")

    print body

    response = "Sorry, something went wrong"

    if step == 0:
        if re.match("register", body, flags=re.IGNORECASE):
            response = "Thanks for registering!  What's your name?"
            step = 1
        else:
            response = "Hi there, welcome to kiddio.  If you'd like to register, please respond with the word 'REGISTER'."
    elif step == 1:
        name = body.strip()
        if name:
            response = session["name"] = name
            response = "Hi %s, what do you normally leave work?  Respond with a time like '6 PM'" % name
            step = 2
        else:
            "Sorry, didn't get your name.  Please respond with your name."


    session["step"] = step

    print response

    resp = twilio.twiml.Response()
    resp.message(response)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)