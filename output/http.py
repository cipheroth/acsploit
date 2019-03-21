import os
import requests
from options import Options
from . import output_common


class Http:
    """Http class."""

    OUTPUT_NAME = 'http'  # exploits can use this internally to whitelist/blacklist supported output formats

    _SEPARATORS = {  # as bytes because
        'newline': '\n',
        'comma': ',',
        'space': ' ',
        'tab': '\t',
        'os_newline': os.linesep.encode(),
        'CRLF': '\r\n',
        'none': ''
    }

    def __init__(self):
        """Initialize the Http class."""
        self.options = Options()
        self.options.add_option('url', 'http://127.0.0.1:80/', 'Host to connect to')
        self.options.add_option('separator', 'newline', 'Separator between elements',
                                list(self._SEPARATORS.keys()), True)
        self.options.add_option('final_separator', False, 'Whether to end output with an instance of the separator')
        self.options.add_option('number_format', 'decimal', 'Format for numbers', ['decimal', 'hexadecimal', 'octal'])

        # TODO - eventually support PUT, DELETE, HEAD, and OPTIONS, since requests easily handles those
        self.options.add_option('http_method', 'GET', 'Type of HTTP request to make', ['POST', 'GET'])
        self.options.add_option('content_type', '', 'Content-Type header for the HTTP request')
        self.options.add_option('url_param_name', 'param', 'Name of URL arg(s) to use')
        self.options.add_option('spread_params', True, 'Put each output in its own URL arg, as opposed to all in one')
        self.options.add_option('use_body', False, 'Put exploit output in body, not URL args')

        self.options.add_option('print_request', False, 'Print HTTP request')
        self.options.add_option('send_request', True, 'Send HTTP request')

    # TODO - eventually allow printing out http response?
    def output(self, output_list):
        """Create an HTTP request and send the payload."""
        url_payload = {}
        data_payload = ''
        separator = output_common.get_separator(self.options['separator'], self._SEPARATORS)

        if self.options['use_body']:
            data_payload = separator.join([self.convert_item(item) for item in output_list])
            if self.options['final_separator']:
                data_payload += separator
        else:
            if self.options['spread_params']:
                url_payload[self.options['url_param_name']] = [self.convert_item(item) for item in output_list]
            else:
                line = separator.join([self.convert_item(item) for item in output_list])
                if self.options['final_separator']:
                    line += separator
                url_payload = {self.options['url_param_name']: line}

        standard_headers = {'User-Agent': 'python-requests', 'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive', 'Accept': '*/*'}
        if self.options['content_type'] != '':
            standard_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=utf-8'

        req = requests.Request(self.options['http_method'], self.options['url'], params=url_payload,
                               headers=standard_headers, data=data_payload)
        prepared = req.prepare()

        if self.options['print_request']:
            self.pretty_print_http(prepared)

        if self.options['send_request']:
            s = requests.Session()
            print('Sending HTTP request...')
            s.send(prepared)    # TODO - eventually wrap this in try/except for ConnectionError?
            print('HTTP request sent.')
            s.close()

    def pretty_print_http(self, prepared_req):
        """Print readable http output."""
        print('-----------START-----------')
        print(prepared_req.method + ' ' + prepared_req.url)
        print(os.linesep.join('{}: {}'.format(k, v) for k, v in prepared_req.headers.items()))

        if self.options['use_body']:
            print(str(os.linesep + '{}').format(prepared_req.body))

        print('------------END------------')

    def convert_item(self, item):
        """Convert output to a bytes type."""
        # NB: this doesn't recurse onto lists
        if type(item) is int:
            if self.options['number_format'] == 'hexadecimal':
                item = hex(item)
            elif self.options['number_format'] == 'octal':
                item = oct(item)

        return str(item)
