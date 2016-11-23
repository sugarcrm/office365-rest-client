# -*- coding: utf-8 -*-
from .backends import DefaultCredentialsBackend
from .services import OutlookService
from .services import CalendarService
from .services import TokenService


class Office365Client(object):
    api_version = 'v1.0'

    def __init__(self, client_id, client_secret,
                 redirect_uri, access_token, refresh_token,
                 user=None, credentials_backend=DefaultCredentialsBackend):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user = user
        self.credentials_backend = credentials_backend
        self.outlook = OutlookService(self)
        self.calendar = CalendarService(self)
        self.token = TokenService(self)

    def save_credentials(self, access_token, refresh_token, expires_at):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.credentials_backend().save_credentials(self.user, access_token, refresh_token, expires_at)

    def save_tokens(self, delta_token, skip_token):
        self.credentials_backend().save_tokens(self.user, delta_token, skip_token)
