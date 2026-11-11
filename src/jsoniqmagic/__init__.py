from jsoniq.session import RumbleSession
from jsoniqmagic.magic import JSONiqMagic

__all__ = ["JSONiqMagic"]

def load_ipython_extension(ipython):
    rumble = RumbleSession.builder.getOrCreate();
    rumble.getRumbleConf().set("runtime.resultsSizeCap", 10);
    ipython.register_magics(JSONiqMagic)