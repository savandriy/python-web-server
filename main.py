from urllib.parse import unquote
import socket
import sys
import os

DEFAULT_PORT = 8000
ADDRESS_FAMILY = socket.AF_INET
SOCKET_TYPE = socket.SOCK_STREAM
REQUEST_QUEUE_SIZE = 5


def open_socket():
    """Creates an open listening socket"""
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else DEFAULT_PORT

    listen_socket = socket.socket(ADDRESS_FAMILY, SOCKET_TYPE)
    # Allow to reuse the same address
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind
    listen_socket.bind(('', port))
    # Activate
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=port))
    return listen_socket


def add_headers(response_without_headers):
    """Add headers to response"""
    headers = 'HTTP/1.1 200 OK\r\nServer: MyServer v0.1\r\n\r\n'
    try:
        return headers + response_without_headers
    except TypeError:
        return headers.encode('utf-8') + response_without_headers


def styles():
    """Add some styles to the HTML"""
    style = """
            <style>
            body{
                background: #000000; 
                background: -webkit-linear-gradient(to left, #000000 , #434343); 
                background: linear-gradient(to left, #000000 , #434343); 
            }
            ul{
                font-size: 20px;
            }
            li, a{
                color: white;
            }
            li{
                transition: font-size 0.3s;
            }
            li:hover{
                font-size: 25px;
            }
            </style>
        """
    return style


def return_index(path='/'):
    """Returns the content of index.html, with HTTP-headers"""
    with open(os.path.join(path if path != '/' else '', 'index.html'), 'rb') as f:
        response = f.read()

    response = add_headers(response)
    return response


def serve():
    """Accept HTTP-requests and return HTTP-responses"""
    listen_socket = open_socket()
    while True:
        client_connection, client_address = listen_socket.accept()
        request_data = client_connection.recv(1024)

        # Parse the request
        try:
            request_line = request_data.splitlines()[0]
        except IndexError:
            print('Got a request with an empty body')

        request_line = request_line.rstrip()
        # Print request
        print(unquote(request_line.decode('utf-8')))
        # Break down the request line into components
        request_method, path, request_version = request_line.split()

        # If there is an 'index.html' file - display it's content
        if os.path.isfile('index.html'):
            response = return_index()
            client_connection.sendall(response)
            client_connection.close()
            continue

        # Find needed file or directory, if '/' display list
        if path.decode('utf-8') == '/':
            response = '<html><head><meta charset="UTF-8"><title>{}</title></head><body><ul>'.format(path.decode('utf-8'))
            all_dir_content = os.listdir()
            for el in all_dir_content:
                response += '<li><a href="{0}">{0}</a></li>'.format(el)
            response += '</ul></body></html>'
            response += styles()
        else:
            # Delete starting /, convert to Unicode, decode special symbols
            new_path = unquote(path[1:].decode('utf-8'))
            if os.path.isfile(new_path):
                with open(new_path, 'rb') as file:
                    response = file.read()
            elif os.path.isdir(new_path):
                response = '<html><head><meta charset="UTF-8"><title>{}</title></head><body><ul>'.format('/' + new_path)

                if 'index.html' in os.listdir(new_path):
                    response = return_index(new_path)
                    client_connection.sendall(response)
                    client_connection.close()
                    continue

                all_dir_content = os.listdir(new_path)
                for el in all_dir_content:
                    response += '<li><a href="{0}/{1}">{1}</a></li>'.format(new_path, el)
                response += '</ul></body></html>'
                response += styles()
            else:
                response = '<h1>Sorry, but there was some kind of error(</h1>'
        try:
            client_connection.sendall(bytes(add_headers(response), 'utf-8'))
        except TypeError:
            client_connection.sendall(add_headers(response))
        client_connection.close()

if __name__ == '__main__':
    serve()