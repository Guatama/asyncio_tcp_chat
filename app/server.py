import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes) -> None:
        decoded_data = data.decode().replace("\r\n", "")

        if self.login is not None:
            self.send_message(decoded_data)
        else:
            if decoded_data.startswith("login:"):
                self.login = decoded_data.replace("login:", "").strip()

                if self.login not in self.server.clients:
                    self.send_history(top=10)
                    self.send_message(f"User {self.login} - connected to chat!", server_msg=True)
                    self.transport.write(f"Hello {self.login}!\n".encode())
                else:
                    self.transport.write(f"Invalid login. {self.login} already using!\n".encode())
                    self.transport.write("^]")
            else:
                self.transport.write("Invalid login. Please, register new login\n".encode())
        if not self.login:
            print(f'SERVER >  Client: {decoded_data}')

    def connection_made(self, transport: transports.BaseTransport) -> None:
        self.server.clients.append(self)
        self.transport = transport
        self.transport.write("WELCOME ON OUR SERVER!\n".encode())
        print('SERVER >  Connection establish')

    def connection_lost(self, exception: Optional[Exception]) -> None:
        self.server.clients.remove(self)

        if not self.login:
            print('SERVER >  Connection lost')
        else:
            print(f'{self.login} >  Connection lost')
            self.send_message(f"User {self.login} - left the server!", server_msg=True)

    def send_message(self, content: str, server_msg=False):
        if server_msg:
            login = 'SERVER'
        else:
            login = self.login

        message = f'{login} >  {content}\n'
        self.server.history.append(message)
        print(message)
        auth_clients = [user for user in self.server.clients if user.login]
        for user in auth_clients:
            user.transport.write(message.encode())

    def send_history(self, top=None):
        if not top:
            hist_msg = ''.join(self.server.history)
        else:
            hist_msg = ''.join(self.server.history[len(self.server.history)-top:])
        self.transport.write(hist_msg.encode())
        print(hist_msg)


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start_server(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print('> Start server...')

        await coroutine.serve_forever()


if __name__ == "__main__":
    process = Server()

    try:
        asyncio.run(process.start_server())
    except KeyboardInterrupt:
        print('> Keyboard Interrupt. Server stopped')
