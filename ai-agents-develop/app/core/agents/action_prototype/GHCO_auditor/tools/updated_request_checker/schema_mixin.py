from pydantic import Field, SecretStr

from app.core.graph.deps.action_deps import ActionDeps


# Mixin with additional fields
class GoogleTokenMixin:
    google_token: SecretStr = Field(
        description="Google access token for Google Drive authentication",
    )


class FindAndDownloadDeps(ActionDeps, GoogleTokenMixin):
    pass
