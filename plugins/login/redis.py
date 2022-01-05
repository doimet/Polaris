# -*-* coding:UTF-8
import os
import socket


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "redis服务口令破解",
        "datetime": "2022-01-02"
    }

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    password=self.target.args.password or os.path.join('data', 'redis_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        socket.setdefaulttimeout(self.target.args.timeout)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.target.value, 6379))
        data = "AUTH {}\r\n".format(password)
        conn.send(data.encode())
        conn.recv(1024)
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 6379,
            'server': 'redis',
            'username': username,
            'password': password
        }
