import logging
import uuid
import traceback
import logging
import socket
import sys
import os
import connexion
from datetime import datetime
from frozendict import frozendict
try:
    import json
except ImportError:
    import simplejson as json
import threading

LM_HTTP_HEADER_PREFIX = "X-Tracectx-"
LOGGING_CONTEXT_KEY_PREFIX = "traceCtx."
LM_HTTP_HEADER_TXNID = "TransactionId".lower()
LM_HTTP_HEADER_PROCESS_ID = "ProcessId".lower()

class LoggingContext(threading.local):

    def __init__(self):
        self.data = {}

    def set_from_headers(self):
        # extract tracing headers such as transactionid, convert their names to logging format and set them in the thread context
        self.data.update(list(map(lambda header: (LOGGING_CONTEXT_KEY_PREFIX + header[0][len(LM_HTTP_HEADER_PREFIX):].lower(), header[1]),
            filter(lambda header: header[0].lower().startswith(LM_HTTP_HEADER_PREFIX.lower()), connexion.request.headers.items()))))

    def set_from_dict(self, d):
        self.data.update(d)

    def get(self, name, default=''):
        return self.data.get(name, default)

    def get_all(self):
        # protect the dictionary from changes - use the setters to do this
        return frozendict(self.data)
    
    def clear(self):
        self.data = {}

class LogstashFormatter(logging.Formatter):

    def __init__(self, message_type='Logstash', tags=None, fqdn=False):
        self.message_type = message_type
        self.tags = tags if tags is not None else []

        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()

    def get_extra_fields(self, record):
        # The list contains all the attributes listed in
        # http://docs.python.org/library/logging.html#logrecord-attributes
        ignore_fields = (
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'extra')

        python_types = (str, bool, dict, float, int, list)

        fields = {}

        for key, value in record.__dict__.items():
            if key not in ignore_fields:
                if value is None:
                    fields[key] = "None"
                elif isinstance(value, python_types):
                    fields[key] = value
                else:
                    fields[key] = repr(value)

        return fields

    def get_debug_fields(self, record):
        fields = {
            'stack_trace': self.format_exception(record.exc_info),
            'lineno': record.lineno,
            'process': record.process,
        }

        # funcName was added in 2.5
        if not getattr(record, 'funcName', None):
            fields['funcName'] = record.funcName

        # processName was added in 2.6
        if not getattr(record, 'processName', None):
            fields['processName'] = record.processName

        return fields

    @classmethod
    def format_source(cls, message_type, host, path):
        return "%s://%s/%s" % (message_type, host, path)

    @classmethod
    def format_timestamp(cls, time):
        tstamp = datetime.utcfromtimestamp(time)
        return tstamp.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (tstamp.microsecond / 1000) + "Z"

    @classmethod
    def format_exception(cls, exc_info):
        return ''.join(traceback.format_exception(*exc_info)) if exc_info else ''

    @classmethod
    def serialize(cls, message):
        return json.dumps(message)

    def format(self, record):
        message = {
            '@timestamp': self.format_timestamp(record.created),
            '@version': '1',
            'message': record.getMessage(),
            'host': self.host,
            'path': record.pathname,
            'tags': self.tags,
            'type': self.message_type,
            'thread_name': record.threadName,
            'level': record.levelname,
            'logger_name': record.name
        }

        # add LM transactional context to log message
        message.update(logging_context.get_all())

        # Add extra fields
        message.update(self.get_extra_fields(record))

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
log_level = os.environ.get('LOG_LEVEL')
if log_level is None:
    log_level = 'INFO'

log_type = os.environ.get('LOG_TYPE')
if log_type is None:
    # "flat" is the default, nothing specific to configure for this
    log_type = 'flat'

if log_type.lower() == 'logstash':
    log_formatter = LogstashFormatter('logstash')
else:
    log_formatter = logging.Formatter()

logging.getLogger().setLevel(log_level)
[handler.setFormatter(log_formatter) for handler in logging.getLogger().handlers]

logging.getLogger('kafka').setLevel('INFO')

logging_context = LoggingContext()