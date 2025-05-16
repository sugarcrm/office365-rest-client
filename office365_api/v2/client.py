# -*- coding: utf-8 -*-
from .services import BatchService, SubscriptionFactory, UserServicesFactory


class MicrosoftGraphClient(object):
    def __init__(self, session):
        self.http = None  # backward compatibility
        self.session = session

        self.users = UserServicesFactory(self)
        self.me = self.users('me')
        self.subscription = SubscriptionFactory(self)()

    def new_batch_request(self, beta=True):
        return BatchService(client=self, beta=beta)
