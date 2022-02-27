# -*-* coding:UTF-8
import asyncio


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "扫描开放端口",
        "datetime": "2022-02-05"
    }

    @cli.options('ip', desc="扫描目标地址", default='{self.target.value}')
    @cli.options('port', desc="扫描开放端口", default='21-23, 25, 53, 80, 135, 139, 143, 161, 389, 443, 445, 512-514,873, 1080, 1090, 1099, 1352, 1433, 1521, 2049, 2100, 2181, 2375, 3000, 3306, 3389, 4000, 4848, 5000, 5432, 5632, 5900, 5984, 6379, 7001, 7002, 8000-9000, 9000-9090, 9200, 9300, 11211, 19121, 19530, 27017, 21018, 28017,50000, 50050, 50070')
    @cli.options('timeout', desc="连接超时时间", type=int, default=1)
    def ip(self, ip, port, timeout):
        port_list = self.string_split(port)
        with self.async_pool() as execute:
            for port in port_list:
                execute.submit(self.custom_task, timeout, ip, port)
            return {'PortList': execute.result()}

    async def custom_task(self, timeout, ip, port):
        self.log.debug(f'start scan port: {port}')
        result = {'ip': ip, 'port': port, 'banner': ''}
        fut = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        try:
            await asyncio.wait_for(self.custom_extract_banner(reader, writer, result), timeout=timeout)
        except asyncio.TimeoutError as te:
            pass
        writer.close()
        self.log.info(f'found open port: {port}')
        return result

    async def custom_extract_banner(self, reader, writer, banner):
        if banner['port'] == 135:
            """ 获取内网IP地址 """
            buffer_v1 = b"\x05\x00\x0b\x03\x10\x00\x00\x00\x48\x00\x00\x00\x01\x00\x00\x00\xb8\x10\xb8\x10\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x00\xc4\xfe\xfc\x99\x60\x52\x1b\x10\xbb\xcb\x00\xaa\x00\x21\x34\x7a\x00\x00\x00\x00\x04\x5d\x88\x8a\xeb\x1c\xc9\x11\x9f\xe8\x08\x00\x2b\x10\x48\x60\x02\x00\x00\x00"
            buffer_v2 = b"\x05\x00\x00\x03\x10\x00\x00\x00\x18\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00"
            writer.write(buffer_v1)
            writer.write(buffer_v2)
            response = await reader.readline()
            response = str(response)[350:-93]

            hostname_list = response.split(r"\x00\x00")
            data = [eval("b'{}'".format(_.replace(r'\x00', '').replace(r'\x07', ''))).decode(
                'raw_unicode_escape') for _ in hostname_list[1:] if _ != '']
            banner['banner'] = 'inner address: ' + ', '.join(data)
        else:
            writer.write(b'hello\n')
            response = await reader.readline()
            banner['banner'] = str(response, encoding='utf-8').strip()
