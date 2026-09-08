from typing import Any, Dict

from .base import BaseService


class AiInsightService(BaseService):
    base_path = 'aiInsights'

    def get(self, insight_id: str) -> Dict[str, Any]:
        path = f'{self.base_path}/{insight_id}'
        method = 'get'
        return self.execute_request(method, path)
