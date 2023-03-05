from socket import socket, AF_INET, SOCK_STREAM
import requests as req


class Biotime(object):
    """
    Biotime main class
    """

    def __init__(self, ip, port, jwt_token="", timeout=60, encoding='UTF-8'):
        """
        Construct a new 'Biotime' object.
        :param ip: server's IP address
        :param port: server's port
        :param encoding: user encoding
        """
        self._server_ip = ip
        self._server_port = port
        self._timout = timeout
        self._jwt_token = jwt_token

    def test_connection(self):
        """
        test connection to server
        :return: bool
        """
        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(self._timout)
        result = sock.connect_ex((self._server_ip, int(self._server_port)))

        return True if result == 0 else False

    def get_jwt_token(self, username, password):
        base_url = 'http://' + self._server_ip + ":" + self._server_port
        uri = '/jwt-api-token-auth/'
        url = base_url + uri
        # header = {"Content-Type": "application/json"} #Adding the header seems to invalidate the req
        body = {"username": username, "password": password}
        res = req.post(url, data=body)
        if res.status_code == 200:
            json_response = res.json()
            self._jwt_token = json_response['token']
            return True
        else:
            return False

    def get_attendances(self, request_params=None):
        """
        Get attendances (transaction list) using the transaction API
        """
        # TODO use authorization param for the jwt token instead of the header (test)
        base_url = 'http://' + self._server_ip + ":" + self._server_port
        uri = '/iclock/api/transactions/'
        url = base_url + uri
        custom_headers = {"Content-Type": "application/json",
                          "Authorization": "JWT {}".format(self._jwt_token)}
        res = req.get(url, params=request_params, headers=custom_headers)
        if res.status_code == 200:
            json_response = res.json()
            return json_response['data']
        else:
            return False
