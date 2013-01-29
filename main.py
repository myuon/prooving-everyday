#! /usr/bin/python
# -*- coding: utf-8 -*-

from google.appengine.ext.webapp import template

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import tweepy
import os, datetime

from setting import *
import cookie

from django.http import HttpResponse, HttpResponseRedirect

def is_dev():
    return os.environ["SERVER_SOFTWARE"].find("Development") != -1

SESSION_EXPIRE = 200
CALLBACK_URL = 'http://localhost:8080/login_callback' if is_dev() else 'http://prooving-everyday.appspot.com/login_callback'

def pair_dic(string):
    elems = string.split(u'&')
    return dict([tuple(e.split(u'=')) for e in elems])

def token_api(access_token):
    token = pair_dic(access_token)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token[u'oauth_token'], token[u'oauth_token_secret'])
    api = tweepy.API(auth_handler=auth)
    return auth, api
    
class MainPage(webapp.RequestHandler):
    def get_usr_info(self, access_token):
        auth, tmp = token_api(access_token)
        username = auth.get_username()
        return {'username':username}
    
    def get(self):
        token = cookie.load_cookie(self)
        message = u''

        if token != 'deleted' and token != '':
            url = u'logout'
            url_linktext = 'Logout'
            
            today = datetime.datetime.today() + datetime.timedelta(days=-1, hours=9)
            message = u'@%s %sに示した定理数: 0(うち自明なもの: 0) #まいにち定理証明' % (self.get_usr_info(token)['username'], unicode(today.strftime('%m-%d')))
        else:
            url = u'login'
            url_linktext = 'Login'
            
        path = os.path.join(os.path.dirname(__file__), 'view/index.html')
        self.response.out.write(template.render(path, {'url': url,
                                                       'url_linktext': url_linktext,
                                                       'login': url == u'logout',
                                                       'message': message
                                                       }))

class RequestToken(db.Model):
    token_key    = db.StringProperty(required=True)
    token_secret = db.StringProperty(required=True)
    
class OAuthLogin(webapp.RequestHandler):
    def get(self):
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, CALLBACK_URL)
        auth_url = auth.get_authorization_url()
        request_token = RequestToken(token_key=auth.request_token.key, token_secret=auth.request_token.secret)
        request_token.put()
        self.redirect(auth_url)

class OAuthLoginCallBack(webapp.RequestHandler):
    def get(self):
        request_token_key = self.request.get("oauth_token")
        request_verifier  = self.request.get('oauth_verifier')
        auth = tweepy.OAuthHandler(CONSUMER_KEY,  CONSUMER_SECRET)
        request_token = RequestToken.gql("WHERE token_key=:1",  request_token_key).get()

        if request_token is None:
            self.redirect('/')
        else:
            auth.set_request_token(request_token.token_key,  request_token.token_secret)
            access_token = auth.get_access_token(request_verifier)
            cookie.set_cookie(self, str(access_token), SESSION_EXPIRE)
            self.redirect('/')
        
class OAuthLogout(webapp.RequestHandler):
    def get(self):
        cookie.del_cookie(self)
        self.redirect('/')

class Update(webapp.RequestHandler):
    def get(self):
        self.redirect('/')

    def post(self):
        auth, api = token_api(cookie.load_cookie(self))

        tweet = self.request.get('content')
        api.update_status(tweet)
        self.redirect('/success')
        
class Success(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'view/posted.html')
        self.response.out.write(template.render(path, {}))

def main():
    application = webapp.WSGIApplication([
                                          ('/', MainPage),
                                          ('/login', OAuthLogin),
                                          ('/login_callback', OAuthLoginCallBack),
                                          ('/logout', OAuthLogout),
                                          ('/tweet', Update),
                                          ('/success', Success)
                                          ],debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

