#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


import webapp2
import logging
import os
import jinja2
import cgi
from google.appengine.ext import ndb
from webapp2_extras import sessions


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': '-\x9a\xf6\xb3\x800kJ\xe1\x97\xea\xbf\xc6d*\xb4:Lo\xb2!\xba\xab\x94',
}


class Subscriber(ndb.Model):
    email = ndb.StringProperty(required=True)
    date = ndb.DateTimeProperty(auto_now_add=True)


def subscription_key(subscriber_name="SUBSCRIPTION"):
    """
    Constructs a Datastore key for a SUBSCRIPTION entity.

    We use name as the key.
    """
    return ndb.Key('EMAIL', subscriber_name)


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


class MainPage(BaseHandler):
    def get(self):
        """Renders a simple api doc with the implemented methods."""
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())

    def post(self):
        subscriber_name = self.request.get('email', "SUBSCRIPTION")
        subscriber = Subscriber(parent=subscription_key(subscriber_name))
        subscriber.email = self.request.get('email')
        subscriber.put()

        # self.session = sessions.get_store(request=self.request)
        self.session["email"] = cgi.escape(self.request.get('email'))
        self.redirect("/thanks")


class MainThanks(BaseHandler):
    def get(self):
        """Renders a simple api doc with the implemented methods."""
        template = JINJA_ENVIRONMENT.get_template('thanks.html')
        email = self.session.get('email')
        if email is not None:
            self.response.write(template.render(name=email))
        else:
            self.redirect("/")


class RobotsHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        self.response.write(open("robots.txt").read())


class HumansHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        self.response.write(open("humans.txt").read())


class CrossdomainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        self.response.write(open("crossdomain.xml").read())


def handle_404(request, response, exception):
    logging.exception(exception)
    # response.write('Sorry, nothing at this URL!')
    response.set_status(404)
    template = JINJA_ENVIRONMENT.get_template('error.html')
    return response.write(template.render())


def handle_500(request, response, exception):
    logging.exception(exception)
    # response.write('A server error occurred!')
    response.set_status(500)
    template = JINJA_ENVIRONMENT.get_template('error.html')
    return response.write(template.render())


debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication(routes=[
    webapp2.Route(r'/subscribe', handler='main.MainPage', name='home'),
    webapp2.Route(r'/', handler='main.MainPage', name='home'),
    webapp2.Route(r'/thanks', handler='main.MainThanks', name='thanks'),
    webapp2.Route(r'/robots.txt', handler='main.RobotsHandler', name='robots'),
    webapp2.Route(r'/humans.txt', handler='main.HumansHandler', name='humans'),
    webapp2.Route(r'/crossdomain.xml', handler='main.CrossdomainHandler', name='humans'),
], debug=debug, config=config)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
