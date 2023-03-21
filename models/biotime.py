from socket import socket, AF_INET, SOCK_STREAM
import requests as req

from typing import Union
from pprint import pprint


class Biotime(object):
    """
    Biotime main class
    """

    def __init__(self, ip, port, jwt_token="", timeout=60, req_params={}):
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
        self._base_url = 'http://' + ip + ":" + port
        self.req_params = req_params

    def _handle_biotime_data_fetch(self, res: req.Response, headers: dict) -> list:
        """
        Used to fetch the whole dataset from a biotime API.
        Biotime limits the number of record sent from it's API (Seems like a pagination system).
        To retreive all the records we go through each response and make a get 
        request to the url present in the 'next' field of each response until the 'next' field is null

        :param res: Response of the initial request
        :param headers: Headers of the initial request
        """
        data = []
        while True:
            res.raise_for_status()
            pprint(res.status_code)
            json_res = False
            if res.status_code == 200:
                json_res = res.json()
                pprint(len(json_res['data']))
                pprint(json_res)
                if json_res['data'] and isinstance(json_res['data'], list):
                    data = data + json_res['data']
                if json_res['next']:
                    url = json_res['next']
                    res = req.get(url, headers=headers)
                else:
                    break
            else:
                break
        return data

    def test_connection(self) -> bool:
        """
        Test connection to Biotime server with sockets
        """
        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(self._timout)
        result = sock.connect_ex((self._server_ip, int(self._server_port)))

        return True if result == 0 else False

    def get_jwt_token(self, username: str, password: str) -> bool:
        """
        Get JWT token using a username and password
        :param username: Username string - Used for the auth process
        :param password: password string - Used for the auth process.
        """
        uri = '/jwt-api-token-auth/'
        url = self._base_url + uri
        # header = {"Content-Type": "application/json"} #Adding the header seems to invalidate the req
        body = {"username": username, "password": password}
        res = req.post(url, data=body)
        if res.status_code == 200:
            json_response = res.json()
            self._jwt_token = json_response['token']
            return True
        else:
            return False

    def get_employees(self, req_params=None) -> list:
        uri = '/personnel/api/employees/'
        url = self._base_url + uri
        headers = {"Content-Type": "application/json",
                   "Authorization": f"JWT {self._jwt_token}"}

        res = req.get(url, params=req_params, headers=headers)

        employees_data = self._handle_biotime_data_fetch(res, headers)
        return employees_data

    def create_employee(self, data) -> bool:
        uri = '/personnel/api/employees/'
        url = self._base_url + uri
        headers = {"Content-Type": "application/json",
                   "Authorization": f"JWT {self._jwt_token}"}

        print('request data : ###########################', str(data))

        res = req.post(url, headers=headers, data=data)

        if res.status_code == 200:
            return True
        else:
            return False

    def get_transactions(self, req_params=None) -> list:
        """
        Get list of transactions using the Biotime transaction API
        :param request_params: Object containing keys/values of parameters to be passed to the url
        """
        uri = '/iclock/api/transactions/'
        url = self._base_url + uri
        # req_params = {'page_size': '10000', 'start_time': '2023-02-01 00:00:00', 'end_time': '2023-02-28 23:59:59'}
        # req_params = {'page_size': '4'}
        headers = {"Content-Type": "application/json",
                   "Authorization": f"JWT {self._jwt_token}"}
        res = req.get(url, params=req_params, headers=headers)

        res.raise_for_status()

        # transactions_data = []
        # print('##################################    First Req ###############################################')
        # pprint(res.status_code)
        # pprint(res.content)
        # if res.status_code != 204:
        #     res_json = res.json()
        #     pprint(res_json)
        #     transactions_data = transactions_data + res_json['data']
        #     if res_json['next']:
        #         sec_res = req.get(res_json['next'], headers=headers)
        #         print('##################################    Second Req ###############################################')
        #         sec_res.raise_for_status()
        #         pprint(sec_res.status_code)
        #         pprint(sec_res.content)
        #         # pprint(sec_res.status_code)
        #     if transactions_data:
        #     # Sort the transaction by punch_time (Works on strings because punch_time follows the Y/M/D H:M:S format)
        #         sorted_transactions_data = sorted(
        #             transactions_data, key=lambda t: t['punch_time'])
        #         return sorted_transactions_data
        #     else:
        #         return []

        # print('req_params #####################' , str(req_params))


        transactions_data = self._handle_biotime_data_fetch(res, headers)
        pprint(transactions_data)
        pprint(len(transactions_data))
        if transactions_data:
            # Sort the transaction by punch_time (Works on strings because punch_time follows the Y/M/D H:M:S format)
            sorted_transactions_data = sorted(
                transactions_data, key=lambda t: t['punch_time'])
            return sorted_transactions_data
        else:
            return []
