# -*-* coding:UTF-8
import math
import urllib.parse


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "name": "ZoomEye",
        "references": ["https://www.zoomeye.org/"],
        "description": "ZoomEye网络空间引擎搜索",
    }

    def dork(self):
        pass

    @cli.command(description='搜索主机')
    @cli.options('dork', help="查询语法", default='{self.target.value}')
    @cli.options('limit', help="限制条数", type=int, default=100)
    @cli.options('timeout', help="请求超时时间", type=int, default=30)
    @cli.options('ip_type', help="获取数据类型", default='ipv4,ipv6')
    def search_host(self, query, limit, timeout, ip_type):
        page, total, page_total, data_list = 1, 0, 0, []
        while True:
            self.log.debug(f'start request page {page}')
            query = urllib.parse.quote(query)
            r = self.request(
                method='get',
                url=f'https://api.zoomeye.org/host/search?query={query}&page={page}&sub_type={ip_type}',
                headers={'API-KEY': self.config.zoomeye.key},
                timeout=(timeout, timeout)
            )
            if r.status_code == 200:
                resp = r.json()
                if resp['total'] == 0:
                    self.log.warn('response data is empty, exit')
                    break
                total = resp['total']
                page_total = int(math.ceil(total / 20.0))
                for one in resp['matches']:
                    if len(data_list) == limit or len(data_list) >= 10000:
                        break
                    data_list.append(
                        {
                            'protocol': one['protocol']['application'],
                            'ip': one['ip'],
                            'port': one['portinfo']['port'],
                            'service': one['portinfo']['service'],
                            'isp': one['geoinfo']['isp'],
                            'country': one['geoinfo']['country']['names']['zh-CN'],
                            'city': one['geoinfo']['city']['names']['zh-CN'],
                            'title': one['portinfo']['title'],
                            'datetime': one['timestamp'].split("T")[0]
                        }
                    )
                else:
                    if page != page_total:
                        page += 1
                        continue
            elif r.status_code == 401:
                raise Exception('Invalid api key')
            else:
                self.log.warn(r.text)
            break
        self.log.info(f'search result total: {total}')
        return {"data_list": data_list}

    @cli.command(description='搜索网站')
    @cli.options('dork', help="查询语法", default='{self.target.value}')
    @cli.options('limit', help="限制条数", type=int, default=100)
    @cli.options('timeout', help="请求超时时间", type=int, default=30)
    def search_web(self, query, limit, timeout):
        page, total, page_total, data_list = 1, 0, 0, []
        while True:
            self.log.debug(f'start request page {page}')
            query = urllib.parse.quote(query)
            r = self.request(
                method='get',
                url=f'https://api.zoomeye.org/web/search?query={query}&page={page}',
                headers={'API-KEY': self.config.zoomeye.key},
                timeout=(timeout, timeout)
            )
            if r.status_code == 200:
                resp = r.json()
                if resp['total'] == 0:
                    self.log.warn('response data is empty, exit')
                    break
                total = resp['total']
                page_total = int(math.ceil(total / 3 / 10.0))
                for one in resp['matches']:
                    if len(data_list) == limit or len(data_list) >= 10000:
                        break
                    data_list.append(
                        {
                            'ip': one['ip'],
                            'url': one['site'],
                            'title': one['title'],
                            'app': [_['chinese'] for _ in one['webapp']],
                            'db': [_['chinese'] for _ in one['db']],
                            'language': one['language'],
                            'server': [_['chinese'] for _ in one['server']],
                            'datetime': one['timestamp'].split("T")[0]
                        }
                    )
                else:
                    if page != page_total:
                        page += 1
                        continue
            elif r.status_code == 401:
                raise Exception('Invalid api key')
            else:
                self.log.warn(r.text)
            break
        self.log.info(f'search result total: {total}')
        return {"data_list": data_list}

    @cli.command(description='搜索图标')
    @cli.options('dork', help="查询语法", default='{self.target.value}')
    @cli.options('limit', help="限制条数", type=int, default=100)
    @cli.options('timeout', help="请求超时时间", type=int, default=30)
    @cli.options('ip_type', help="获取数据类型", default='ipv4,ipv6')
    def search_icon(self, query, limit, timeout, ip_type):
        return self.search_host('iconhash:' + query, limit, timeout, ip_type)

    @cli.command(description='搜索整数')
    @cli.options('dork', help="查询语法", default='{self.target.value}')
    @cli.options('limit', help="限制条数", type=int, default=100)
    @cli.options('timeout', help="请求超时时间", type=int, default=30)
    @cli.options('ip_type', help="获取数据类型", default='ipv4,ipv6')
    def search_cert(self, query, limit, timeout, ip_type):
        return self.search_host('ssl:' + query, limit, timeout, ip_type)

    @cli.command(description='搜索域名')
    @cli.options('dork', help="查询语法", default='{self.target.value}')
    @cli.options('limit', help="限制条数", type=int, default=100)
    @cli.options('timeout', help="请求超时时间", type=int, default=30)
    def search_domain(self, query, limit, timeout):
        page, page_total, data_list = 1, 0, []
        while True:
            self.log.debug(f'start request page {page}')
            query = urllib.parse.quote(query)
            r = self.request(
                method='get',
                url=f'https://api.zoomeye.org/domain/search?q={query}&page={page}&type=0',
                headers={'API-KEY': self.config.zoomeye.key},
                timeout=(timeout, timeout)
            )
            if r.status_code == 200:
                resp = r.json()
                page_total = int(math.ceil(resp['total'] / 3 / 10.0))
                for one in resp['list']:
                    if len(data_list) == limit or len(data_list) >= 10000:
                        break
                    data_list.append(
                        {
                            'ip': one['ip'],
                            'subdomain': one['name'],
                            'datetime': one['timestamp']
                        }
                    )
                else:
                    if page != page_total:
                        page += 1
                        continue
            elif r.status_code == 401:
                raise Exception('Invalid api key')
            else:
                self.log.warn(r.text)
            break
        return {"data_list": data_list}
