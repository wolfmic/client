from .UpdaterBase import UpdaterBase
import logging
logger = logging.getLogger(__name__)

class FeaturedModFiles(UpdaterBase):
    def __init__(self, id, version):
        UpdaterBase.__init__(self, '/featuredMods/'+ id + '/files/' + str(version))

    def requestData(self):
        return self.request({}, self.handleData)
    
    def handleData(self, message):
        return message


class FeaturedModId(UpdaterBase):
    def __init__(self):
        UpdaterBase.__init__(self, '/data/featuredMod')
    
    def requestData(self, queryDict):
        return self.request(queryDict, self.handleData)

    def handleData(self, message):
        return message[0]['id']