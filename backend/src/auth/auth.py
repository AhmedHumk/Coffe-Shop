import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import const

# my auth0 data is in const model

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

## Auth Header
        
def get_token_auth_header():
    # lets get our Authorization Token from the header
    authorization_token = request.headers.get("Authorization", None)
    # if we dont have a valid authorization_token
    # then raise an error
    if not authorization_token:
        raise AuthError({
            "code": "Authorization_header_is_empty",
            "description": "No Authorization header included"
            }, const.Err_Unauth)
    # lets split our authorization_token and check
    # if we have Bearer and token
    split_auth_token = authorization_token.split()
    # before we do anything lets check split_auth_token length
    # we excpect to have a length equal 2
    # if the length is smaller than 2 then raise an error
    if len(split_auth_token) < 2:
        raise AuthError({
            "code": "invalid_authorization_length",
            "description": "invalid Authorization header length"
            }, const.Err_Unauth)
    # if everything is fine lets set
    # our Bearer and token variables
    # [0] for Bearer - [1] for token
    Bearer_val = split_auth_token[0]
    token_val = split_auth_token[1]
    # lets check our Bearer_val if it has
    # a word of bearer
    if Bearer_val.lower() != "bearer":
        raise AuthError({
            "code": "invalid_header_bearer",
            "description": "the bearer provided is invalid"
            }, const.Err_Unauth)
    # if everything is fine then
    # return the token_val
    return token_val


# check premissions
def check_permissions(permission, payload):
    # lets check if we have,
    # permissions in our playload
    if "permissions" not in payload:
        raise AuthError({
            "code": "invalid_playload",
            "description": "permissions is not included"
            }, const.Err_badrequest)

    if permission not in payload['permissions']:
        raise AuthError({
            "code": "invalid_playload",
            "description": "permissions is not included"
            }, const.Err_badrequest)
    # if everything is fine return true
    return True
    

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
# Verify jwt decode
def verify_decode_jwt(token):
    # fetch my RSA key from Auth0
    # based on Identity and Authentication lesson
    Auth0UrL = "https://{}/.well-known/jwks.json".format(const.AUTH0_DOMAIN)
    getjsonData = urlopen(Auth0UrL)
    # Read our fetched json data
    data_json = json.loads(getjsonData.read())
    header_verfication = jwt.get_unverified_header(token)
    # lets Verfiy the header
    if "kid" not in header_verfication:
        raise AuthError({
            "code": "invalid_header",
            "description": "header is not included"
            }, const.Err_Unauth)
        
    myrskey = {}
    # lets loop throw data_json
    for key in data_json["keys"]:
        if key["kid"] == header_verfication["kid"]:
            myrskey = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
                }
    # if we dont have a key then
    # raise Error
    if not myrskey:
        raise AuthError({
            "code": "invalid_header",
            "description": "header is not included"
            }, const.Err_Unauth)
    # if we have a key then
    # lets try to decode our token
    try:
        payload = jwt.decode(
            token,
            myrskey,
            algorithms=const.ALGORITHM,
            audience=const.API_AUDIENCE,
            issuer="https://{}/".format(const.AUTH0_DOMAIN)
            )
        return payload
    
    except jwt.ExpiredSignatureError:
        raise AuthError({
            "code": "invalid_token",
            "description": "this token is invalid"
            }, const.Err_Unauth)
    except jwt.JWTClaimsError:
        raise AuthError({
            "code": "invalid_claims",
            "description": "invalid claims"
            }, const.Err_Unauth)
    except Exception as E:
        print(E)
        raise AuthError({
            "code": "invalid_header",
            "description": "invalid header"
            }, const.Err_Unauth)

    
        
'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
