from distutils.dist import Distribution

class SQDistribution(Distribution):
    def __init__(self, attrs=None):
        self.cs_files = None
        self.js_libs = None
        Distribution.__init__(self, attrs)
