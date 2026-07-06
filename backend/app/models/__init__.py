"""ORM models package.

Importing this package registers every model on ``Base.metadata`` so ``init_db``
can create their tables. New features add a module here and re-export below.
"""

from app.models.consumption import ConsumptionLog
from app.models.user import ActivityLevel, Goal, Profile, Sex, User

__all__ = ["User", "Profile", "Sex", "ActivityLevel", "Goal", "ConsumptionLog"]
