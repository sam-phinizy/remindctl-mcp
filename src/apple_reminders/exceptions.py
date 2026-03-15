class RemindersError(Exception):
    """Base exception for apple-reminders operations."""


class RemindersNotFoundError(RemindersError):
    """Raised when the remindctl binary is not found."""


class RemindersTimeoutError(RemindersError):
    """Raised when a remindctl command times out."""


class RemindersAuthError(RemindersError):
    """Raised when remindctl lacks Reminders authorization."""
