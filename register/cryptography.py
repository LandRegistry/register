from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from base64 import b64decode
from flask import current_app
import re


class CryptographicSigning(object):
    """Pseudo extension which gives persistent signer instances

    """
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    # Currently don't need to do anything here
    def init_app(self, app):
        pass

    def validate_signature(self, payload, signature, payload_hash=None):
        current_app.logger.info("Validate the signature")
        if not hasattr(self, 'cyptosign_validate'):
            self.cyptosign_validate = self._create_validator()
        sha256 = None
        if payload_hash:
            current_app.logger.info("Checking supplied payload hash")
            hash_match = re.search('sha-256:(.+)', payload_hash)
            if not hash_match:
                current_app.logger.warning("Invalid payload hash supplied")
                return False, "Invalid hash string '{0}'.".format(payload_hash)
            current_app.logger.info("Found payload hash with valid format")
            sha256 = hash_match.group(1)
        current_app.logger.info("Checking supplied signature")
        sig_match = re.search('rs256:(.+)', signature)
        if not sig_match:
            current_app.logger.warning("Invalid signature supplied")
            return False, "Invalid signature string '{0}'.".format(signature)
        current_app.logger.info("Found signature with valid format")
        digest = SHA256.new()
        digest.update(payload.encode('UTF-8'))
        if sha256 and digest.hexdigest() != sha256:
            current_app.logger.warning("Supplied hash does not match calculated hash")
            return False, "Supplied hash does not match calculated hash."
        if self.cyptosign_validate.verify(digest, b64decode(sig_match.group(1))):
            current_app.logger.info("Signature and payload match")
            return True, "Signature and payload match."
        current_app.logger.warning("Signature and payload do not match")
        return False, "Signature and payload do not match."

    def _create_validator(self):
        current_app.logger.info("Create validator")
        key_data = open(current_app.config['PUBLIC_KEY'], 'rb').read()
        rsakey = RSA.importKey(key_data, current_app.config['PUBLIC_PASSPHRASE'])
        signer = PKCS1_v1_5.new(rsakey)
        return signer
