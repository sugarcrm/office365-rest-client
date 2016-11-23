# -*- coding: utf-8 -*-
class CredentialsBackendBase(object):
    pass


class DefaultCredentialsBackend(CredentialsBackendBase):

    def save_credentials(self, *args, **kwargs):
        pass

    def save_tokens(self, *args, **kwargs):
        pass
