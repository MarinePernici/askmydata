class InvalidInvitationError(Exception):
    pass


class InvitationExpiredError(Exception):
    pass


class InvalidAccessRequestError(Exception):
    pass


class PendingAccessRequestExistsError(Exception):
    pass


class ActiveInvitationExistsError(Exception):
    pass


class AccountAlreadyExistsError(Exception):
    pass
