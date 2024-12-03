from redpepper.requests import RequestError


async def call(conn, **kwargs):
    raise RequestError("This function is not implemented.")


# This is so that the request can be identified in error messages
call.__qualname__ = "registerVPN"
