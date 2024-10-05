import socket
import re
from http import HTTPStatus

HOST = '127.0.0.1'
PORT = 4500


def prepare_server(skt:socket):
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.bind((HOST, PORT))
    skt.listen()

def get_request_method(request_string:str)->str:
    # Метод запроса идет первым словом во входной строке
    return re.match('\\w+\\b',request_string).group()


def get_host_address(host_string:str)->list:
    host_d = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', host_string).group()
    host_d= re.split(':', host_d)
    return host_d


def set_response_status(parameters: str):
    # Проверяем наличие параметра status
    res = (re.search(r'status=\w+[&\s]', parameters))
    # При отсутствии возвращаем OK
    if res is None:
        return HTTPStatus.OK, HTTPStatus.OK.name
    res = res.group()
    # Находим значение параметра status
    res = re.search(r'=(\w*)[&\s]', res).group(1)
    # Если число -преобразуем в числовое значение, если нет - возвращаем OK
    try:
        code_status = int(res)
    except ValueError:
        return HTTPStatus.OK, HTTPStatus.OK.name
    # Если такого кода статуса не существует - возвращаем OK
    if code_status not in list(HTTPStatus):
        return HTTPStatus.OK, HTTPStatus.OK.name
    else:
        return code_status, HTTPStatus(code_status).phrase


def set_additional_headers(splitted_data):
    # Входные данные - все заголовки запроса
    headers_dict = dict()
    # Если в заголовках только метод и host - возвращаем пустое значение
    if len(splitted_data) <=2:
        return None
    for item in splitted_data[2:]:
        if len(item) > 0:
            temp = re.split(':', item)
            headers_dict[temp[0]] = temp[1]
    return headers_dict


def create_response(list_headers:list)->str:
    f_request_method, f_address, f_port, f_status, f_status_text, f_additional_headers = list_headers
    output_string = \
f"""HTTP/1.1 {status_code} {status_text}\n
Request Method: {list_headers[0]}\r
Request Source: ('{f_address}', {f_port})\r
Response Status: {f_status} {f_status_text}\r
"""
    for key, item in f_additional_headers.items():
        output_string += f'{key}:{item}\r\n'
    return output_string

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
        prepare_server(sk)

        while True:
            print('Waiting for connection')
            conn, addr = sk.accept()
            with conn:
                print("connected by", addr)
                # Receive
                try:
                    data = conn.recv(4096)
                except ConnectionError:
                    print(f"Client unexpectedly closed while receiving")
                    break
                headers_data = list()
                data_ = re.split('\r\n', data.decode())
                request_method = get_request_method(data_[0])
                headers_data.append(request_method)
                host_data = get_host_address(data_[1])
                headers_data.extend(host_data)
                status_code, status_text = set_response_status(data_[0])
                headers_data.extend((status_code, status_text))
                headers_data.append(set_additional_headers(data_))
                final_string= create_response(headers_data)
                data_for_send = final_string.encode()
                try:
                    conn.sendall(data_for_send)
                except ConnectionError:
                    print(f"Client closed, cannot send")
                    break
            print('Disconnected by ', {addr})