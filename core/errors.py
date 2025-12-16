class SusAIError(Exception):
    pass

class DataSourceError(SusAIError):
    pass

class ParseError(SusAIError):
    pass

class IndexError(SusAIError):
    pass
