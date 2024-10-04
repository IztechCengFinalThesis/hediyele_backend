from typing import Any

from exceptions.app import BadGatewayExc


class ExternalConnectionErrorExc(BadGatewayExc):
    """External connection error."""

    def __init__(self, service_name: str, payload: Any = None):
        super().__init__()
        self.message = f"Unable to connect to the service - {service_name}"
        self.payload = payload


class ExternalFailResponseExc(BadGatewayExc):
    """External failure response."""

    def __init__(self, service_name: str, status_code: int, payload: Any):
        super().__init__()
        self.message = f"Service: {service_name} - not a successful response"
        self.payload = {
            "data": payload,
            "status_http": status_code,
        }
