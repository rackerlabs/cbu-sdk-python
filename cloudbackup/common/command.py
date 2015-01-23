"""
Rackspace Cloud Backup Command API
"""


class Command(object):
    """
    Base class for defining HTTP REST API calls
    """

    def __init__(self, sslenabled, apihost, uripath):
        """
        Initialize the Command Object
          sslenabled - True if using HTTPS; otherwise False
          apihost - server to use for API calls
          uripath - HTTP(S) Path for the REST API being defined
        """
        self.body = {}
        self.headers = {}
        self.headers['X-RCBU-Integration-User-Agent'] = 'RCBU-Integration-Tests/1.0'
        self.headers['User-Agent'] = self.headers['X-RCBU-Integration-User-Agent']
        self.uri = ''
        self.apihost = apihost
        self.__ReInit(sslenabled, uripath)

    @property
    def ApiHost(self):
        """API Host"""
        return self.apihost

    @property
    def Body(self):
        """HTTP Message Body Data"""
        return self.body

    @property
    def Headers(self):
        """HTTP Message Header Data"""
        return self.headers

    @property
    def Uri(self):
        """HTTP URI"""
        return self.uri

    def ReInit(self, sslenabled, uripath):
        """
        Reinitialize the HTTP URI with the new specification
        Useful for objects that provide access to multiple HTTP REST API calls
        """
        # By default there is no HTTP Body Data
        self.body = None
        # By default we set the HTTP Content Type
        self.headers = {}
        self.headers['Content-Type'] = 'application/json; charset=utf-8'
        # HTTP or HTTPS
        if (sslenabled):
            self.uri = "https://" + self.apihost + uripath
        else:
            self.uri = "http://" + self.apihost + uripath

    __ReInit = ReInit
