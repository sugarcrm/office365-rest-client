# -*- coding: utf-8 -*-


from .factories.user_factory import UserServicesFactory
from .services import BatchService, ChatService, SubscriptionService


class MicrosoftGraphClient(object):
    def __init__(self, session):
        self.http = None  # backward compatibility
        self.session = session

        self.users = UserServicesFactory(self)
        self.me = self.users('me')
        self.subscription = SubscriptionService(self, '')
        self.chats = ChatService(self, '')

    def new_batch_request(self, beta=True):
        return BatchService(client=self, beta=beta)
