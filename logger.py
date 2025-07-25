import logging
import json
import socket
import time
import traceback

class LogstashFormatter(logging.Formatter):
    def __init__(self, app_name="fastapi"):
        self.app_name = app_name
        self.hostname = socket.gethostname()
        super(LogstashFormatter, self).__init__()

    def format(self, record):
        # Create a basic log dictionary
        log_record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "app": self.app_name,
            "host": self.hostname,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "path": record.pathname,
            "lineno": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields from record.props if it exists
        if hasattr(record, 'props'):
            for key, value in record.props.items():
                log_record[key] = value
                
        return json.dumps(log_record)

class JsonTcpHandler(logging.Handler):
    """Handler that sends logs as JSON over TCP"""
    
    def __init__(self, host, port):
        super(JsonTcpHandler, self).__init__()
        self.host = host
        self.port = port
        self.sock = None
        
    def connect(self):
        """Connect to the Logstash server"""
        if self.sock is not None:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        
    def emit(self, record):
        try:
            if self.sock is None:
                self.connect()
                
            msg = self.format(record) + '\n'  # Add newline as separator
            self.sock.sendall(msg.encode('utf-8'))
        except (socket.error, socket.timeout) as e:
            self.sock = None  # Force reconnection next time
            self.handleError(record)
        except Exception:
            self.handleError(record)
            
    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        super(JsonTcpHandler, self).close()

def setup_logging(app_name="fastapi", logstash_host="logstash", logstash_port=5000):
    """Set up logging with console and Logstash handlers"""
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate logs by clearing existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Logstash handler with JSON formatter
    logstash_handler = JsonTcpHandler(logstash_host, logstash_port)
    logstash_formatter = LogstashFormatter(app_name)
    logstash_handler.setFormatter(logstash_formatter)
    logger.addHandler(logstash_handler)
    
    return logger