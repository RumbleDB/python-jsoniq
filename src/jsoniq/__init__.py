from jsoniq.session import RumbleSession
from jsoniq.magic import JSONiqMagic

__all__ = ["RumbleSession", "JSONiqMagic"]

def load_ipython_extension(ipython):
    rumble = RumbleSession.builder.getOrCreate();
    ipython.register_magics(JSONiqMagic)