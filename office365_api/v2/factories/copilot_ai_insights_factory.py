from .base_factory import BaseFactory
from ..services import AiInsightService


class CopilotAiInsightsFactory(BaseFactory):
    """Reaches aiInsights, the one Graph resource whose path needs `copilot/` *before*
    `users/{user_id}`, unlike every other online-meeting resource (which nests under
    `users/{user_id}/onlineMeetings/{meeting_id}` via UserServicesFactory)."""

    def __call__(self, user_id: str, meeting_id: str) -> AiInsightService:
        return AiInsightService(self.client, f'copilot/users/{user_id}/onlineMeetings/{meeting_id}')
