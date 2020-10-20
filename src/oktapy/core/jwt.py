from py_jwt_verifier import PyJwtVerifier, PyJwtException
import jwt
import time


class JWT(object):
    def validate(self, jwt):
        try:
            PyJwtVerifier(jwt)
        except PyJwtException as e:
            print(f"Exception caught. Error: {e}")

    def getSignedJWT(self, privateKey, clientid, aud, algorithm='RS256'):
        # Algo : RS256, RS384, RS512, ES256, ES384, ES512
        now = int(time.time())
        token = {'iss': clientid,
                 'sub': clientid,
                 'aud': aud,
                 'iat': now,
                 'exp': now + 3600}
        encoded = jwt.encode(token, privateKey, algorithm)
        return encoded
