import uasyncio as asyncio
import machine
import binascii
import os
import sys
import io
import json


def get_exception_str(exception):
    exception_io = io.StringIO()
    sys.print_exception(exception, exception_io)
    exception_io.seek(0)
    result = exception_io.read()
    exception_io.close()
    return result


async def http_request(domain, url, data, headers=()):
    reader, writer = await asyncio.open_connection(domain, 80)
    method = 'GET'
    if data:
        method = 'POST'
        body_extra =  \
            "Content-Length: {}\r\n\r\n{}".format(
                len(data.encode('latin-1')),
                data,
            )
    else:
        body_extra = '\r\n'
    headers_str = ''.join(
        "{}: {}\r\n".format(k, v) for k, v in headers.items()
    )

    query = \
        "{} {} HTTP/1.0\r\n" \
        "Host: {}\r\n" \
        "{}" \
        "{}".format(
            method,
            url,
            domain,
            headers_str,
            body_extra,
        )
    try:
        await writer.awrite(query.encode('latin-1'))
        while True:
            line = await reader.readline()
            if not line:
                break
    except:
        pass


class SentryClient:
    def __init__(self, project_id, key):
        self.project_id = project_id
        self.key = key

    async def send_exception(self, exception):
        domain = 'sentry.io'
        url_tpl = '/api/{}/store/'
        url = url_tpl.format(self.project_id)
        json_data = (
            '{'
            '"event_id": "%(event_id)s",'
            '"exception": {"values":[{"type": "%(type)s","value": '
            '%(value)s,"module": "%(module)s"}]},'
            '"tags": {'
            '"machine_id": "%(machine_id)s", '
            '"platform": "%(platform)s",'
            '"os.name": "%(os_name)s",'
            '"os.version": "%(os_version)s"},'
            '"extra": {"stacktrace": %(stacktrace)s}'
            '}' %
            {
                'event_id': binascii.hexlify(os.urandom(16)).decode(),
                'type': exception.__class__.__name__,
                'value': json.dumps(
                    exception.args[0] if exception.args else '',
                ),
                'module': exception,
                'stacktrace': json.dumps(get_exception_str(exception)),
                'machine_id': binascii.hexlify(machine.unique_id()).decode(),
                'platform': sys.platform,
                'os_name': sys.implementation.name,
                'os_version': ".".join(
                    str(x) for x in sys.implementation.version
                ),
            }
        )
        return await http_request(
            domain,
            url,
            json_data,
            {
                "Content-Type": "application/json",
                "X-Sentry-Auth": "Sentry sentry_version=7, sentry_key={}, "
                "sentry_client=sentry-micropython/0.1".format(self.key)
            },
        )
