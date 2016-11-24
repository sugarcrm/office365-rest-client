# -*- coding: utf-8 -*-
from .backends import DefaultCredentialsBackend
from .services import OutlookService
from .services import CalendarService
from .services import TokenService


class Office365Client(object):
    api_version = 'v1.0'

    def __init__(self, client_id, client_secret, redirect_uri,
                 access_token, refresh_token, user_id=None,
                 credentials_backend=DefaultCredentialsBackend):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_id = user_id
        self.credentials_backend = credentials_backend
        self.outlook = OutlookService(self)
        self.calendar = CalendarService(self)
        self.token = TokenService(self)

    def save_credentials(self, access_token, refresh_token, **kwargs):
        self.credentials_backend().save_credentials(access_token, refresh_token, **kwargs)
        self.access_token = access_token
        self.refresh_token = refresh_token
