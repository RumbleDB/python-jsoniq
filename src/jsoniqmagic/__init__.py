from jsoniq.session import RumbleSession
from jsoniqmagic.magic import JSONiqMagic

__all__ = ["JSONiqMagic"]

def load_ipython_extension(ipython):
    ipython.register_magics(JSONiqMagic)