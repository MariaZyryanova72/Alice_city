from flask import Flask, request
import logging
import json
import random
from geo import get_geo_info
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.

cities = {
    '965417/de71d85855b422e5dd80': 'москва',
    '1533899/8ab3e4a6a992a1453144': 'москва',
    '1533899/699dea3e824324e4e3b7': 'нью-йорк',
    '1521359/1c05b8c7469cda19f408': 'нью-йорк',
    "1533899/6d3f1817d5f81c118d41": 'париж',
    '213044/42f9cb4413e36ef2fcbc': 'париж'
}

# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    res['response']['end_session'] = False
    res['response']['text'] = ''
    user_id = req['session']['user_id']
    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'city': '',
            'country': '',
            'first_name': None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name[0].upper() + first_name[1:]
            image_id = random.choice([key for key in cities.keys()])
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = f'{ sessionStorage[user_id]["first_name"] }, отгадай город =)'
            res['response']['card']['image_id'] = image_id
            sessionStorage[user_id]['city'] = image_id

    elif sessionStorage[user_id]['country'] != '':
        if req['request']['original_utterance'].lower() == sessionStorage[user_id]['country'].lower():
            res['response']['text'] = f'Правильно, { sessionStorage[user_id]["first_name"] }! Сыграем ещё?'
            sessionStorage[user_id]['city'] = ''
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Покажи город на карте',
                    "url": f"https://yandex.ru/maps/?mode=search&text={ sessionStorage[user_id]['city'] }",
                    'hide': True
                }
            ]
            sessionStorage[user_id]['city'] = ''
            sessionStorage[user_id]['country'] = ''
        else:
            res['response']['text'] = f'Неверно, { sessionStorage[user_id]["first_name"] }. Попробуй ещё раз!'

    elif sessionStorage[user_id]['city'] != '':
        city_name = get_city(req)
        if city_name is None:
            res['response']['text'] = f' { sessionStorage[user_id]["first_name"] },' \
                                      f' я не знаю такого города. Попробуй еще разок!'

        else:
            if cities[sessionStorage[user_id]['city']].lower() == city_name.lower():
                cities.pop(sessionStorage[user_id]['city'])
                if cities == {}:
                    res['response']['text'] = f' { sessionStorage[user_id]["first_name"] }, вы выиграли!\nПока-пока!'
                    res['response']['end_session'] = True
                    return

                res['response']['text'] = f'Правильно,  { sessionStorage[user_id]["first_name"] }!' \
                                          f' А в какой стране этот город?'
                sessionStorage[user_id]['country'] = get_geo_info(city_name)
            else:
                res['response']['text'] = f'Неверно,  { sessionStorage[user_id]["first_name"] }. Попробуй ещё раз!'

    else:
        if req['request']['command'] == 'Да':
            image_id = random.choice([key for key in cities.keys()])
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = f'{ sessionStorage[user_id]["first_name"] }, отгадай город =)'
            res['response']['card']['image_id'] = image_id
            sessionStorage[user_id] = {
                'city': image_id,
                'country': ''
            }
        elif req['request']['command'] == 'Нет':
            res['response']['text'] = 'Пока!'
            res['response']['end_session'] = True
        elif req['request']['command'] == 'Покажи город на карте':
            res['response']['text'] = f'{ sessionStorage[user_id]["first_name"] }, играем дальше?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }]


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run(port=5005)
