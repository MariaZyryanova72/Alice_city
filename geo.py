import requests


def get_geo_info(city_name):
    url = "https://geocode-maps.yandex.ru/1.x/"

    params = {
        'geocode': city_name,
        'format': 'json',
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b"
    }

    response = requests.get(url, params)
    json = response.json()
    return json['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'] \
            ['GeocoderMetaData']['AddressDetails']['Country']['CountryName']
