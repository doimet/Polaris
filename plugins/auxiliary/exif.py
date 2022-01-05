# -*-* coding:UTF-8
import exifread
from geopy.geocoders import Nominatim


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "获取图片中隐藏的信息",
        "datetime": "2021-12-31"
    }

    def image(self) -> dict:
        with open(self.target.value, 'rb') as f:
            exif_dict = exifread.process_file(f)
        lon_ref = exif_dict.get('GPS GPSLongitudeRef', '')
        if not lon_ref:
            return {}
        lon_ref = lon_ref.printable
        lon = exif_dict['GPS GPSLongitude'].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
        lon = float(lon[0]) + float(lon[1]) / 60 + float(lon[2]) / float(lon[3]) / 3600
        if lon_ref != "E":
            lon = lon * (-1)
        lat_ref = exif_dict['GPS GPSLatitudeRef'].printable
        lat = exif_dict['GPS GPSLatitude'].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
        lat = float(lat[0]) + float(lat[1]) / 60 + float(lat[2]) / float(lat[3]) / 3600
        if lat_ref != "N":
            lat = lat * (-1)
        date = exif_dict['EXIF DateTimeOriginal'].printable
        location = Nominatim().reverse(str(lat) + ', ' + str(lon))
        address = location.address
        return {
            '经度': lon,
            '纬度': lat,
            '拍摄时间': date,
            '地理位置': address
        }
