# Курсовая работа "Резервное копирование"
'''
Программа производит резервное копирование фотографий из профиля Вконтакте с наилучшим качеством на Яндекс диск

Входные данные:
user_ids_vk.txt     - Id Vk
token_vk.txt        - токен Vk
token_yandex.txt    - token Yandex
amount_photo = 5    - количество фотографий для резервного копирования
folder_name_ya      - имя создаваемой папки на Яндекс диске

Выходные данные:
data.txt            - файл для вывода списка файлов в формате json
Папка на Яндекс диске с сохраненными фотографиями
'''

import requests
import json


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, user_ids, amount_photo, version):
        self.params = {
            'access_token': token,
            'user_ids': user_ids,
            'v': version
        }
        self.amount_photo = amount_photo

    def get_data_user_vk(self):
        ''' Метод возвращает данные о фотографиях с профиля Vk в формате json'''

        data_url = self.url + 'photos.get'
        data_params = {
            'owner_id': self.params['user_ids'],
            'album_id': 'profile',
            #'album_id': 'wall',
            'extended': '1',
            'v': '5.131'
        }

        res = requests.get(data_url, params={**self.params, **data_params}).json()
        return res['response']['items']

    def selection_quality_photo(self, sizes_photo):
        '''
        Метод функция выбирает из списка экземпляров sizes_photo фотографию с наилучшим качеством
        и возвращает её type и <URL>
        '''

        quality_photo = 0
        for size in sizes_photo:
            if size['height'] * size['width'] >= quality_photo:
                quality_photo = size['height'] * size['width']
                type_photo = size['type']
                url_photo = size['url']
        return type_photo, url_photo

    def data_filtering(self):
        '''
        Метод возвращаает данные о фотографиях профиля в виде списка словарей:
        [{'likes': число лайков, 'type': тип фото, 'url': <URL фото на Vk>}, ...,{}]
        '''

        # Получаем данные с профиля Vk
        data_user = self.get_data_user_vk()
        # Выбираем заданное amount_photo количество фотографий
        data_user = data_user[:amount_photo]

        list_photo = []
        for item in data_user:
            likes_photo = item['likes']['count']
            # Выбираем фотографию с максимальным качеством
            type_photo, url_photo = self.selection_quality_photo(item['sizes'])
            list_photo.append({'likes': likes_photo, 'type': type_photo, 'url': url_photo})
        return list_photo


def get_list_files(list_photo):
    '''
    Функция из списка list_photo формирует:
    1. Список в формате [{'file_name': file_name, 'size': size},...,{}]
    2. Список в формате [{'file_name': file_name, 'url': url_file_vk},...,{}]
    '''

    output_list_files = []
    list_files = []
    files = []

    for photo in list_photo:
        index = 0
        # Формируем имя файла
        file_name = str(photo['likes']) + '.jpg'
        # Если имя файла существует добавляем к имени _индекс
        while file_name in files:
            index += 1
            file_name = str(photo['likes']) + '_' + str(index)+'.txt'
        files.append(file_name)
        output_list_files.append({'file_name': file_name, 'size': photo['type']})
        list_files.append({'file_name': file_name, 'url': photo['url']})
    return output_list_files, list_files


class YaUploader:
    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json', #??????
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def _get_upload_link(self, disk_file_path):
        upload_url = 'https://cloud-api.yandex.net:443/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {'path': disk_file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=headers, params=params)
        #pprint(response.json())
        return response.json()

    def create_folder_ya(self, folder_name):
        ''' Метод создает папку на Яндекс диске'''

        upload_url = 'https://cloud-api.yandex.net:443/v1/disk/resources'
        headers = self.get_headers()
        params = {'overwrite': 'false'}
        response = requests.put(f'{upload_url}?path={folder_name}', headers=headers, params=params)
        if response.status_code == 201:
            # Логирование процесса записи на яндекс диск
            print(f'Папка {folder_name} успешно создана на яндекс диске')

    def upload(self, list_files, folder_ya):
        """Метод загружает файлы по списку list_files на яндекс диск"""
        for file in list_files:
            file_name = file['file_name']

            # создаем папку на яндекс диске
            self.create_folder_ya(folder_name=folder_ya)

            disk_file_path = folder_ya + '/' + file_name  # Если папка существует на яндекс диске
            response_href = self._get_upload_link(disk_file_path=disk_file_path)
            href = response_href.get('href', '')
            data = requests.get(file['url'])
            response = requests.put(href, data=data.content)
            response.raise_for_status()
            if response.status_code == 201:
                # Логирование процесса записи на яндекс диск
                print(f'Файл {file_name} успешно записан в папку {folder_ya} на Яндекс диск')

if __name__ == '__main__':
    # Получаем токен Vk
    with open('token_vk.txt', 'r') as file_object:
        token_vk = file_object.read().strip()
    # Получаем user id Vk
    with open('user_ids_vk.txt', 'r') as file_object:
        user_ids = file_object.read().strip()
    # Получаем токен на Яндекс диске
    with open('token_yandex.txt', 'r') as f:
        token_ya = f.readline()
    # Задаем количество сохраняемых фотографий
    amount_photo = 5
    # Задаем имя папки  на Яндекс диске
    folder_name_ya = 'my_photo_vk'
    # Задаем версию Vk
    version = '5.131'

    # Создаем экземпляр класса VkUser()
    vk_client = VkUser(token=token_vk, user_ids=user_ids, amount_photo=amount_photo, version=version)
    # Получаем список заданного amount_photo количества фотографий наилучшего качества
    list_photo = vk_client.data_filtering()
    # Формируем списки
    output_list_files, list_files = get_list_files(list_photo)
    # Выводим требуемый список output_list_files в json файл  data.txt
    with open('data.txt', 'w', encoding='utf-8') as file_obj:
       json.dump(output_list_files, file_obj, ensure_ascii=False)
       print('Список файлов с указанием размера сохранен в формате json в файл data.txt')

    # Создаем экземпляр класса YaUploader()
    uploader = YaUploader(token_ya)
    # Сохраняем фотографии на Яндекс диск
    uploader.upload(list_files, folder_name_ya)




