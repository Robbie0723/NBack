import logging
import random
import boto3
from datetime import datetime
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

client = boto3.client('dynamodb')
sns_client = boto3.client('sns')
sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



def nback(answer, session_attr):
    # global score, used, level, new_level

    # print("current score is {}" .format(len(session_attr['used'])))

    
    colors = ["red", 'blue', 'green', 'yellow', 'orange', 'purple']
    
    if len(session_attr['used']) == 0:
        session_attr['used'].insert(0, random.choice(colors))
        session_attr['used'].insert(0, random.choice(colors))
        session_attr['used'].insert(0, random.choice(colors))
        return "Here are the first colors: {}. {}. {}" .format(session_attr['used'][2], session_attr['used'][1], session_attr['used'][0])
    else:
        session_attr['used'].insert(0, random.choice(colors))

    
    session_attr['guesses'] = len(session_attr['used']) -3
    
    
    if answer == session_attr['used'][session_attr['level'] + 1]:
            session_attr['score'] +=1
            if session_attr['score'] < 5:
                session_attr['level'] = 1
                return session_attr['used'][0]
            elif session_attr['score'] >= 5 and session_attr['score'] < 10:
                session_attr['level'] = 2
                if session_attr['new_level']['two'] == False:
                    session_attr['new_level']['two'] = True
                    session_attr['new_level']['one'] = False
                    return "Congratulations!  You are now at level 2.  You scored 5 points in {} tries.  You will need to remember the third color now." \
                    "  The newest color is {}.".format(session_attr['guesses'], session_attr['used'][0])
                else:
                    return session_attr['used'][0]
            elif session_attr['score'] >= 10 and session_attr['score'] < 15:
                session_attr['level'] = 3
                if session_attr['new_level']['three'] == False:
                    session_attr['new_level']['three'] = True
                    session_attr['new_level']['two'] = False
                    session_attr['new_level']['one'] = False
                    return "You are now at level 3. Very impressive!  You scored 10 points in {} tries.  You will need to remember the fourth color now." \
                    "  The newest color is {}." .format(session_attr['guesses'], session_attr['used'][0])
                else:
                    return session_attr['used'][0]
            elif session_attr['score'] >= 15:
                session_attr['level'] = 4
                if session_attr['new_level']['four'] == False:
                    session_attr['new_level']['four'] = True
                    session_attr['new_level']['three'] = False
                    session_attr['new_level']['two'] = False
                    session_attr['new_level']['one'] = False
                    return "Amazing!  You reached level 4.  You scored 15 points in {} tries.  You will need to remember the fifth color now." \
                    "  The newest color is {}." .format(session_attr['guesses'], session_attr['used'][0])
                else:
                    return session_attr['used'][0]
            else:
                return session_attr['used'][0]
    else:
        return session_attr['used'][0]
        
        

def send_email(userid):
    message = 'Nback skill is being used by the following user: {}' .format(userid)
    response = sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:?????????????:alexa_skills_email',
        Message= message,
        Subject='NBack skill has been activated',
        MessageStructure='string'
    )
    return response

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        #send email notifying me that game is activated.
        user_id = handler_input.request_envelope.session.user.user_id
        send_email(user_id)

        #creating a session attribute
        session_attr = handler_input.attributes_manager.session_attributes
        
        session_attr['used'] = []
        session_attr['score'] = 0
        session_attr['level'] = 1
        session_attr['new_level']= {"one": True, "two": False, "three": False, "four": False}
        begin = nback(None, session_attr)
        speech_text = "Welcome to the N-Back game. {}" .format(begin)
        reprompt = "Please pick a color."
        handler_input.response_builder.speak(speech_text).ask(reprompt).set_card(
            SimpleCard("Start N-Back game", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response




class WhatIsMyScore(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("Score")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        speech_text = "The  current level is {}, and the current score is {}.  If you would like to continue, please say the next color," \
        " or say stop to exit." .format(session_attr['level'], session_attr['score'])
        sc = "Current level is {} and current score is {}." .format(session_attr['level'], session_attr['score'])
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard(sc, speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response



class GameonHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("Playing")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        answer = slots['Color'].value
        session_attr = handler_input.attributes_manager.session_attributes
        speech_text = nback(answer, session_attr)
        
        reprompt = "I did not hear your response.  What is the color?"
        handler_input.response_builder.speak(speech_text).ask(reprompt).set_card(
            SimpleCard("Game On", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "This is an N-Back game.  The point of this game is to remember the color said a certain number back."\
        "  For example, if you are on level 1, you will want to remember the second to last color said."\
        "  If you are on level 2, you will want to remember the third most recent color.  For more information, please see "\
        "the Wikipedia page on N-Back."

        handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(
                "Instructions:\nhttps://en.wikipedia.org/wiki/N-back", speech_text))
        return handler_input.response_builder.response


def add_item(user_id, session_attr):
    time = str(datetime.now())

    session_attr['guesses'] = len(session_attr['used'])-3
    
    response = client.put_item(
        Item={
            'TimeStamp': {
                'S': time,
            },
            'Guesses': {
                'N': str(session_attr['guesses']),
            },
            'Level': {
                'N': str(session_attr['level'])
            },
            'Score': {
                'N': str(session_attr['score'])
            },
            'UserID':{
                'S':user_id
            }
        },
        ReturnConsumedCapacity='TOTAL',
        TableName='N-Back',
)




class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))
                

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Thank you for playing.  Goodbye!"
        
        user_id = handler_input.request_envelope.session.user.user_id
        session_attr = handler_input.attributes_manager.session_attributes
        add_item(user_id, session_attr)  
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Ending N-Back game", speech_text))
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "I'm sorry, I couldn't hear that.  Please repeat. "
        reprompt = "I'm sorry, I couldn't hear that.  Please repeat. "
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "Sorry, there was some problem. Please try again."
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(GameonHandler())
sb.add_request_handler(WhatIsMyScore())

sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()