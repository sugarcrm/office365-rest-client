# -*- coding: utf-8 -*-
from office365.services import OutlookService
from office365.services import TokenService


class Office365Client(object):
    api_version = 'v1.0'

    def __init__(self, client_id, client_secret, redirect_uri, access_token, refresh_token):
        self.outlook = OutlookService(self)
        self.token = TokenService(self)
