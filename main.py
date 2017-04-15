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


def convert_to_proper_unicode(*args):
    """Convert multiple byte-coded strings to readable Unicode strings"""
    return [unquote(arg.decode('utf-8')) for arg in args]


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


def return_index_html(path='/'):
    """Returns the content of index.html, with HTTP-headers"""
    with open(os.path.join(path if path != '/' else '', 'index.html'), 'rb') as f:
        response = f.read()

    response = add_headers(response)
    return response


def return_directory_html(path):
    """Return an HTML-page displaying list of directory contents + styles"""
    response = '<html><head><meta charset="UTF-8">\
    <title>{}</title></head><body><ul>'.format(path if path == '/' else '/' + path)
    all_dir_content = os.listdir(os.getcwd() if path == '/' else path)
    for el in all_dir_content:
        if path == '/':
            response += '<li><a href="{0}">{0}</a></li>'.format(el)
        else:
            response += '<li><a href="{0}/{1}">{1}</a></li>'.format(path, el)
    response += '</ul></body></html>'
    response += styles()
    return response


def parse_request(request_data):
    """Parse the request data, return the request line"""
    request_line = request_data.splitlines()[0]
    return request_line.rstrip().split()


def serve():
    """Accept HTTP-requests and return HTTP-responses"""
    listen_socket = open_socket()
    while True:
        client_connection, client_address = listen_socket.accept()
        request_data = client_connection.recv(1024)
        # Parse the request
        try:
            request_method, path, request_version = parse_request(request_data)
        except IndexError:
            response = '<h1>Sorry, but there was some kind of error(</h1>'
            client_connection.sendall(bytes(add_headers(response), 'utf-8'))
            client_connection.close()
            continue
        # Print the request line
        print(*convert_to_proper_unicode(request_method, path, request_version))
        # Convert path to proper Unicode
        path = convert_to_proper_unicode(path)[0]
        # Delete the starting slash to work properly
        path = path if path == '/' else path[1:]

        # If there is an 'index.html' file - display it's content
        if os.path.isfile('index.html'):
            response = return_index_html()
            client_connection.sendall(response)
            client_connection.close()
            continue

        # If requested a file - send it's content
        if os.path.isfile(path):
            with open(path, 'rb') as file:
                response = file.read()
        # If requested a directory - send an HTML-page displaying a list of directory contents
        elif os.path.isdir(path):
            # If there is an 'index.html' file in directory - display it's content
            if 'index.html' in os.listdir(path):
                response = return_index_html(path)
                client_connection.sendall(response)
                client_connection.close()
                continue
            response = return_directory_html(path)
        else:
            response = '<h1>Sorry, but there was some kind of error(</h1>'

        # Send the response data
        try:
            client_connection.sendall(bytes(add_headers(response), 'utf-8'))
        except TypeError:
            client_connection.sendall(add_headers(response))
        client_connection.close()

if __name__ == '__main__':
    serve()
