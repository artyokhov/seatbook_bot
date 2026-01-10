class BookingError(Exception):
    pass


class BookingConflictError(BookingError):
    pass
