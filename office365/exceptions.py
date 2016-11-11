# -*- coding: utf-8 -*-
class UnknownFilterException(Exception):

    def __init__(self):
        super(UnknownFilterException, self).__init__(
            'A filter should be provided.'
        )


class ClientException(Exception):
    pass
