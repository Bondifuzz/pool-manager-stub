from logging import LoggerAdapter


class PrefixedLogger(LoggerAdapter):
    def process(self, msg, kwargs):
        return f"{self.extra['prefix']} {msg}", kwargs
