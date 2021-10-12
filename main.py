from datetime import datetime
import os
from pathlib import Path
import json
import requests
from tokens import vk_token


def log_message(text):
    print(f'{datetime.now().strftime(f"[%H:%m:%S]")} {text}')


def create_folder(token, folder_name):
    url = "https://cloud-api.yandex.net/v1/disk/resources/"

    headers = {
        "Accept": "application/json",
        "Authorization": f"OAuth {token}"
    }

    params = {
        'path': folder_name
    }

    requests.put(url=url, params=params, headers=headers)


def upload(token, local_filename, remote_filename):
    headers = {
        "Accept": "application/json",
        "Authorization": f"OAuth {token}"
    }

    params = {
        'path': remote_filename
    }

    url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    link = requests.get(url=url, params=params, headers=headers).json()
    if 'href' in link:
        try:
            r = requests.put(url=link['href'], data=open(local_filename, 'rb'), params=params, headers=headers)
            print(f"После отправки файла на Яндекс диск, получили от сервера код ответа:", r.status_code)
        except FileNotFoundError:
            print("Файл с указанным именем не найден!")
    else:
        print(link['message'])


log_message("Создаем папку photos для фотографий")
Path("photos").mkdir(parents=True, exist_ok=True)

while True:
    try:
        vk_id = int(input("Введите id пользователя: "))
        break
    except ValueError:
        print("Введен некорректный id! Попробуйте еще раз...")

parameters = {
    'owner_id': vk_id,
    'extended': 1,
    'v': '5.82',
    'album_id': 'profile',
    'access_token': vk_token
}

log_message("Отправляем запрос на сервер ВК")

result = requests.get("https://api.vk.com/method/photos.get", params=parameters).json()
log_message("Получен ответ от сервера")

info = []

if ('response' in result) and ('items' in result['response']) and result['response']['items']:
    log_message("Начинаем обработку...")
    count = 1
    for item in result['response']['items']:
        size = item['sizes'][-1]['height']
        filename = f"{count}_{item['likes']['count']}.jpg"
        with open(os.path.join('photos', filename), 'wb') as f:
            url = item['sizes'][-1]['url']
            f.write(requests.get(url).content)
            log_message(f"Файл № {count} с фотографией был записан")
            info.append({'file_name': filename, 'size': size})
        count += 1

    with open('info.json', 'w') as f:
        json.dump(info, f, ensure_ascii=False, indent=4)
    log_message("Файл json с информацией о фотографиях был записан")

    ya_disk_token = input("Введите token API Яндекс Диска: ")

    photos_folder = 'photos'

    log_message("Создаем папку photos на Яндекс диске")
    create_folder(ya_disk_token, photos_folder)

    log_message("Начинаем загрузку фотографий на Яндекс Диск")

    count = 1
    for file in os.listdir(photos_folder):
        local = os.path.join(photos_folder, file)
        remote = f"{photos_folder}/{file}"
        upload(ya_disk_token, local, remote)
        log_message(f"Файл № {count} обработан")
        count += 1
else:
    print("Некорректный профиль ВК (страница удалена, профиль является закрытым, нет фотографий и т.п.")
