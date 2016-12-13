import os
import sys
import asyncio

import bluetooth


def handle_stdin(client_sock):
    data = sys.stdin.readline()
    if data:
        client_sock.send(data)
        print('> ', end='', flush=True)


def read_data(client_sock):
    data = client_sock.recv(1024)
    return data.decode('utf-8')


async def handle_console_output(client_sock, queue):
    print('> ', end='', flush=True)
    while True:
        data = await queue.get()
        print('\rReceived> : ', data, '\n> ', end='', flush=True)


async def listen_for_data(client_sock, loop, queue):
    while True:
        try:
            bluetooth.btcommon.BluetoothError
            data = await asyncio.ensure_future(loop.run_in_executor(None, read_data, client_sock), loop=loop)
            asyncio.ensure_future(queue.put(data), loop=loop)
        except bluetooth.btcommon.BluetoothError as e:
            return False

async def handle_client_data(client_sock, loop, queue):
    output_cor = asyncio.ensure_future(handle_console_output(client_sock, queue), loop=loop)
    result = await listen_for_data(client_sock, loop, queue)
    if not result:
        output_cor.cancel()
    return result


def main(server_sock):
    client_sock = None
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)
    try:
        while True:
            print('\n***   Waiting for connection...   ***')
            client_sock, address = server_sock.accept()
            print('\n***   Accepted connection from {}   ***\n'.format(address[0]))
            # Run main loop
            loop.add_reader(sys.stdin, handle_stdin, client_sock)
            listener = asyncio.ensure_future(handle_client_data(client_sock, loop, queue), loop=loop)
            loop.run_until_complete(listener)
            if not listener.result():
                loop.remove_reader(sys.stdin)
                print('\n*** Connection closed by the client!! ***')
    except KeyboardInterrupt:
        print('\n***   Server stopped by user   ***')

    loop.close()
    client_sock and client_sock.close()


if __name__ == '__main__':
    # Init server
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(('', 0))
    server_sock.listen(1)
    # Run main loop
    os.system('clear')
    main(server_sock)
    # Close server connection
    server_sock.close()
