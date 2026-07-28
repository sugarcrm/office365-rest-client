import urllib.parse
from typing import Any, Dict, Optional, Tuple

from .base import BaseService


class ChatService(BaseService):
    base_path = 'chats'

    def messages(self, chat_id: str, max_entries: int = 50) -> Tuple[Dict[str, Any], Optional[str]]:
        path = f'{self.base_path}/{urllib.parse.quote(chat_id, safe="")}/messages'
        query_params: Dict[str, Any] = {'$top': max_entries}
        resp = self.execute_request('get', path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link
