# -*- coding: utf-8 -*-
import requests

from .services import BatchService, SubscriptionFactory, UserServicesFactory


class MicrosoftGraphClient(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.http = None # backward compatibility
        self.session = requests.Session()        
        self.credentials.apply(self.session.headers)

        self.users = UserServicesFactory(self)
        self.me = self.users('me')
        self.subscription = SubscriptionFactory(self)()

    def new_batch_request(self):
        return BatchService(client=self)
