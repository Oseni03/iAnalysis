import enum

class EmailType(enum.Enum):
    ACCOUNT_CONFIRMATION = "account_confirmatin"
    PASSWORD_RESET = "password_reset"
    SUBSCRIPTION_ERROR = "subscription_error"
    TRIAL_EXPIRES_SOON = "trial_expires_soon"