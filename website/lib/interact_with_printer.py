import socket

pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def try_to_connect_to_printer(ip):
    good = True
    errors = []
    PORT = 9100
    BUFFER_SIZE = 1024
    for i in range(3):
        try:
            pSocket.connect((ip, PORT))
            break
        except (ConnectionRefusedError,OSError):
            good = False

    if good == False:
        errors.append("Error, couldn't reach printer with that IP address")

    return good, errors

def cancel_print():
    # Canceling all the jobs on the printer
    zpl = '''~JA'''
    pSocket.send(bytes(zpl,"utf-8"))
    pSocket.close()

def send_label_to_printer(zpl):
    pSocket.send(bytes(zpl,"utf-8"))
