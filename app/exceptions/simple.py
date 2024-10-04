from exceptions.app import ConflictExc


class SimpleAlreadyExistExc(ConflictExc):
    """Simple Already Exist exception."""

    message = "Simple Already Exist"
