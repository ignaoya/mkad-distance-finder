class GeocoderError(Exception):
    """Base class for geocoder conversion exceptions."""
    pass


class YandexError(GeocoderError):
    """Base class for other Yandex API related exceptions."""
    pass


class YandexValueError(YandexError):
    """Exception used when the request uses an invalid parameter or value."""
    def __init__(self):
        self.message = "Address could not be parsed due to invalid value."
        super().__init__(self.message)


class YandexValidationError(YandexError):
    """Exception used when the request uses an invalid API key."""
    def __init__(self):
        self.message = "Invalid API key provided."
        super().__init__(self.message)
