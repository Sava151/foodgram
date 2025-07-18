# Описание.
## Проект реализует API на базе **Django rest_framework**.
### Какого то глубокого смысла или пользы он не несет это просто учебный проект 

# Установка. 
## Следуйте следующим команда для установки и развертывание проекта у себя локально 
### Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/Sava151/foodgram
```
```
cd foodgram/
```
### Cоздать и активировать виртуальное окружение:
#### Рекомендуется использовать python 3.9
```
py -3.9 -m venv venv
```
```
source venv/Scripts/activate
```
#### Уточнение имеющихся версий python 
```
py -0
```
#### Уточнение версии по умолчанию
```
python --version 
```
### Установить зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
### Выполнить миграции
```
python manage.py migrate
```
### Запустить проект
```
python manage.py runserver
```

### Некоторые примеры запросов 
1. [Get запрос список пользователей](https://foodgram151.zapto.org/api/users/)
2. [Get запрос список рецептов](https://foodgram151.zapto.org/api/recipes/)
2. [Get запрос список ингредиентов с фильтрацией](https://foodgram151.zapto.org/api/ingredients/?name=sometext)


# Стек технологий 
## Версия Python 3.9
## Сторонние библиотеки
* Django
* djangorestframework
* django-filter  
* djangorestframework_simplejwt
* djoser

### Ссылка на сам проект
[Foodgram](https://foodgram151.zapto.org/recipes)
### Об авторе
[Sava151](https://github.com/Sava151)