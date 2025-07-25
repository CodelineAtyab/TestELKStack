import logging
import json
import socket
import time
from typing import Dict, Any

class LogstashFormatter(logging.Formatter):
    def __init__(self, app_name: str = "fastapi"):
        self.app_name = app_name
        self.hostname = socket.gethostname()
        super(LogstashFormatter, self).__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "app": self.app_name,
            "host": self.hostname,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "props"):
            log_data.update(record.props)

        return json.dumps(log_data)

class LogstashHandler(logging.handlers.SocketHandler):
    def __init__(self, host: str, port: int, app_name: str = "fastapi"):
        super(LogstashHandler, self).__init__(host, port)
        self.formatter = LogstashFormatter(app_name)

def setup_logging(app_name: str = "fastapi", logstash_host: str = "logstash", logstash_port: int = 5000):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Logstash handler
    logstash_handler = LogstashHandler(logstash_host, logstash_port, app_name)
    logger.addHandler(logstash_handler)
    
    return logger