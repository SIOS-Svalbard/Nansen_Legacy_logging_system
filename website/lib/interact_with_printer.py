import socket
import time

def try_to_connect_to_printer(ip):
    good = True
    errors = []
    PORT = 9100
    BUFFER_SIZE = 1024
    for i in range(3):
        try:
            pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pSocket.connect((ip, PORT))
            pSocket.close()
            break
        except (ConnectionRefusedError,OSError):
            good = False

    if good == False:
        errors.append("Error, couldn't reach printer with that IP address")

    return good, errors


# def try_to_connect_to_printer(ip):
#     PORT = 9100
#     BUFFER_SIZE = 1024
#     retries = 3
#     delay_between_retries = 2  # 2 seconds delay between retries
#
#     for i in range(retries):
#         try:
#             pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             pSocket.settimeout(5)  # Set a timeout for the connection attempt
#             pSocket.connect((ip, PORT))
#             pSocket.close()
#             return True, []  # Successfully connected, return immediately
#         except (ConnectionRefusedError, OSError, socket.timeout):
#             time.sleep(delay_between_retries)
#
#     errors = ["Error, couldn't reach printer with that IP address"]
#     return False, errors

def cancel_print(ip):
    # Canceling all the jobs on the printer
    zpl = '''~JA'''
    PORT = 9100
    pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pSocket.connect((ip, PORT))
    pSocket.send(bytes(zpl,"utf-8"))
    pSocket.close()

def send_label_to_printer(zpl, ip):
    PORT = 9100
    pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pSocket.connect((ip, PORT))
    pSocket.send(bytes(zpl,"utf-8"))
    pSocket.close()
