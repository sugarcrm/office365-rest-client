# -*- coding: utf-8 -*-
import httplib2
from .services import UserServicesFactory


class MicrosoftGraphClient(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.http = httplib2.Http()
        self.credentials.authorize(self.http)

        self.users = UserServicesFactory(self)
        self.me = self.users('me')
