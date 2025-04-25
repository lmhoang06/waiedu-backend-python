import jwt
from datetime import datetime, timedelta, timezone


def generate_jwt(payload: dict, secret: str, expiry: int = 86400) -> str:
    """
    Generate a JWT token.

    :param payload: The payload to encode in the token.
    :param secret: The secret key to sign the token.
    :param expiry: The expiry time in seconds (default is 86400 seconds).
    :return: Encoded JWT token as a string.
    """
    expiration_time = datetime.now(tz=timezone.utc) + timedelta(seconds=expiry)
    payload['exp'] = expiration_time
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_jwt(token: str, secret: str) -> dict:
    """
    Decode a JWT token.

    :param token: The JWT token to decode.
    :param secret: The secret key to verify the token.
    :return: Decoded payload as a dictionary.
    """
    return jwt.decode(token, secret, algorithms=["HS256"])