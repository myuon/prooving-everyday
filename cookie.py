#! /usr/bin/python
# -*- coding: utf-8 -*-

import datetime

def set_cookie(self, data, expire):
    expires_date = datetime.datetime.utcnow() + datetime.timedelta(expire)
    expires_formatted = expires_date.strftime("%d %b %Y %H:%M:%S GMT")

    self.response.headers.add_header(
       'Set-Cookie', 
       'access_token=' + data + '; expires='+ expires_formatted + ';path=/;')

def load_cookie(self):
    return self.request.cookies.get('access_token', '')

def del_cookie(self):
    set_cookie(self, "deleted", 10)
