# -*- coding: utf-8 -*-
import httplib2
from ssl import TLSVersion
from urllib3.contrib import pyopenssl

from .services import UserServicesFactory, SubscriptionFactory, BatchService

pyopenssl.inject_into_urllib3()

class MicrosoftGraphClient(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.http = httplib2.Http(tls_minimum_version=TLSVersion.TLSv1_3, tls_maximum_version=TLSVersion.TLSv1_3)
        self.credentials.authorize(self.http)

        self.users = UserServicesFactory(self)
        self.me = self.users('me')
        self.subscription = SubscriptionFactory(self)()

    def new_batch_request(self):
        return BatchService(client=self)
