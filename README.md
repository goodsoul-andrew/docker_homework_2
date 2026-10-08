# 1
Продолжите Flask-приложение первой пары в отдельном репозитории: добавьте постоянные заметки в PostgreSQL и счётчик в Redis. Опишите приложение, входной сервис Nginx, БД и кеш в `compose.yaml`, запустите стек на своей Linux-ВМ. Закрепите зависимости приложения, отделите установку зависимостей от копирования кода. Добавьте healthcheck БД и кеша и настройте ожидание app через `depends_on` с `condition: service_healthy`. Подтвердите готовность выводом `docker compose ps` и запросом к приложению.
```commandline
docker compose up --build -d
```
```
 ✔ Image docker_homework_2-app         Built                                                                                                                                                          1.2s
 ✔ Network docker_homework_2_default   Created                                                                                                                                                        0.0s
 ✔ Container docker_homework_2-db-1    Healthy                                                                                                                                                        5.3s
 ✔ Container docker_homework_2-redis-1 Healthy                                                                                                                                                        2.3s
 ✔ Container docker_homework_2-app-1   Started    
```
```commandline
docker compose ps
```
```commandline
NAME                        IMAGE                   COMMAND                  SERVICE   CREATED         STATUS                          PORTS
docker_homework_2-app-1     docker_homework_2-app   "python app.py"          app       2 minutes ago   Up About a minute (unhealthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
docker_homework_2-db-1      postgres:16             "docker-entrypoint.s…"   db        2 minutes ago   Up About a minute (healthy)     5432/tcp
docker_homework_2-redis-1   redis:7-alpine          "docker-entrypoint.s…"   redis     2 minutes ago   Up About a minute (healthy)     6379/tcp
```
```commandline
curl -X POST http://localhost:8000/note   -H "Content-Type: application/json"   -d '{"content": "заметка"}'
 curl -X POST http://localhost:8000/note   -H "Content-Type: application/json"   -d '{"content": "вторая заметка"}'
```
```
{"content":"заметка","id":1,"notes_count":1}
{"content":"вторая заметка","id":2,"notes_count":2}
```
![первое задание](/images/docker_hw2_1.png)

# 2
Подключите к БД именованный volume по пути, соответствующему выбранной версии образа. Запишите контрольную заметку, замените контейнер БД с подключением прежнего тома и запросом SQL или через приложение подтвердите её сохранность. Счётчик Redis может быть временным: явно опишите, какое состояние сохраняете, а какое допускаете потерять.
```commandline
docker compose up --build -d
```
```
[+] up 6/6
 ✔ Image docker_homework_2-app         Built                                                                                                                                                          1.1s
 ✔ Volume docker_homework_2_pgdata     Created                                                                                                                                                        0.0s
 ✔ Network docker_homework_2_default   Created                                                                                                                                                        0.0s
 ✔ Container docker_homework_2-redis-1 Healthy                                                                                                                                                        2.3s
 ✔ Container docker_homework_2-db-1    Healthy                                                                                                                                                        5.3s
 ✔ Container docker_homework_2-app-1   Started   
```
```commandline
curl -X POST http://localhost:8000/note   -H "Content-Type: application/json"   -d '{"content": "контрольная заметка"}'
```
```commandline
{"content":"контрольная заметка","id":1,"notes_count":1}
```
```commandline
docker compose stop db && docker compose rm db
```
```
[+] stop 1/1
 ✔ Container docker_homework_2-db-1 Stopped                                                                                                                                                           0.2s
? Going to remove docker_homework_2-db-1 Yes
[+] remove 1/1
 ✔ Container docker_homework_2-db-1 Removed    
```
```commandline
curl http://localhost:8000/notes
```
```html
<!doctype html>
<html lang=en>
<title>500 Internal Server Error</title>
<h1>Internal Server Error</h1>
<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
```
```commandline
docker compose up -d db
```
```commandline
curl http://localhost:8000/notes
```
```
[{"content":"контрольная заметка","id":1}]
```
```commandline
curl -X POST http://localhost:8000/note   -H "Content-Type: application/json"   -d '{"content": "вторая заметка"}'
```
```commandline
{"content":"контрольная заметка","id":1,"notes_count":2}
```
![второе задание](/images/docker_hw2_2.png)
Счётчик можно не сохранять, его можно восстановить просто сделав запрос в базу данных
# 3
Сделайте холодный бэкап БД: остановите все сервисы, которые могут писать в неё, и саму БД, сохранив том обычным `docker compose down` без `-v`. Через временный контейнер создайте архив содержимого тома в каталоге вне исходного volume. После успешного создания архива удалите только том собственного учебного проекта, создайте его заново и восстановите архив. Поднимите тот же стек с тем же образом БД и подтвердите контрольную заметку запросом. В отчёте приложите команды остановки, архивирования, удаления, восстановления и ключевой вывод проверки. Создание архива без проверки восстановления не считается завершённой частью задания.
```commandline
docker compose down
```
```commandline
[+] down 4/4
 ✔ Container docker_homework_2-app-1   Removed                                                                                                                                                       10.2s
 ✔ Container docker_homework_2-redis-1 Removed                                                                                                                                                        0.2s
 ✔ Container docker_homework_2-db-1    Removed                                                                                                                                                        0.1s
 ✔ Network docker_homework_2_default   Removed  
```
```commandline
docker volume ls | grep pgdata
```
```commandline
local     docker_homework_2_pgdata
```
```commandline
docker run --rm -v docker_homework_2_pgdata:/pgdata -v "$(pwd)/backups":/backups alpine sh -c 'tar czf /backups/pgdata.tar.gz -C /pgdata .'
```
```commandline
tar tzf backups/pgdata.tar.gz | head -5
```
```commandline
./
./postgresql.conf
./pg_replslot/
./pg_serial/
./pg_multixact/
```
```commandline
docker volume rm docker_homework_2_pgdata
```
```commandline
docker_homework_2_pgdata
```
```commandline
docker volume ls | grep pgdata
```
```commandline

```
```commandline
docker volume create docker_homework_2_pgdata
```
```commandline
docker_homework_2_pgdata
```
```commandline
docker run --rm -v docker_homework_2_pgdata:/pgdata -v "$(pwd)/backups":/backups alpine sh -c 'tar xzf /backups/pgdata.tar.gz -C /pgdata'
docker compose up -d && docker compose ps
```
```commandline
WARN[0000] volume "docker_homework_2_pgdata" already exists but was not created by Docker Compose. Use `external: true` to use an existing volume 
[+] up 4/4
 ✔ Network docker_homework_2_default   Created                                                                                                                                                        0.0s
 ✔ Container docker_homework_2-redis-1 Healthy                                                                                                                                                        2.3s
 ✔ Container docker_homework_2-db-1    Healthy                                                                                                                                                        5.3s
 ✔ Container docker_homework_2-app-1   Started                                                                                                                                                        5.4s
NAME                        IMAGE                   COMMAND                  SERVICE   CREATED         STATUS                   PORTS
docker_homework_2-app-1     docker_homework_2-app   "python app.py"          app       6 seconds ago   Up Less than a second    0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
docker_homework_2-db-1      postgres:16             "docker-entrypoint.s…"   db        6 seconds ago   Up 5 seconds (healthy)   5432/tcp
docker_homework_2-redis-1   redis:7-alpine          "docker-entrypoint.s…"   redis     6 seconds ago   Up 5 seconds (healthy)   6379/tcp
```
```commandline
curl http://localhost:8000/notes
```
```commandline
[{"content":"контрольная заметка","id":1},{"content":"вторая заметка","id":2}]
```
![task 3.1](/images/docker_hw2_3_1.png)
![task 3.2](/images/docker_hw2_3_2.png)
![task 3.3](/images/docker_hw2_3_3.png)

# 4
Разделите стек минимум на две пользовательские сети: front для Nginx и Flask, back для Flask, БД и кеша. Публикуйте только входной сервис. Из Nginx проверьте отсутствие DNS-имени БД и отказ прямого TCP-подключения к её внутреннему IP и порту; из приложения подтвердите успешный доступ к БД и кешу. Не подключайте входной сервис к back ради прохождения проверки. Объясните, почему Flask в двух сетях выполняет свои запросы к БД, но не становится автоматическим IP-маршрутизатором.

```commandline
docker compose up --build -d
```
```commandline
docker compose exec nginx sh -c 'getent hosts db; echo "exit=$?"'
```
`getent` позволяет извлекать записи из системных баз данных, нам нужно из `hosts`  
`echo "exit=$"` выводит код ошибки из прошлой команды после "exit="
```commandline
exit=2
```
запись не найдена
```commandline
docker compose exec app sh -c 'getent hosts db'
```
```commandline
172.20.0.3      db
```
а в контейнере app эта запись есть, он может обращаться и к db
```commandline
docker compose exec nginx sh -c 'nc -zv -w 3 172.20.0.3 5432; echo "exit=$?"'
```
попытка tcp подключения к известному порту, на котором работает db
```
nc: 172.20.0.3 (172.20.0.3:5432): Operation timed out
exit=1
```
не получилось
```commandline
curl http://localhost:8080/health
```
при GET на этот эндпоинт приложение проверяет доступность db и redis и возвращает рзультаты
```
{"db":"ok","redis":"ok","status":"ok"}
```
![task 4](/images/docker_hw2_4.png)
Чтобы app стал маршрутизатором, нужно разрешить пересылать пакеты между сетевыми интерфейсами (у него их два, один для front, другой для back), и чтобы у других были настроены маршруты через него

# 5
Вынесите изменяемые значения в переменные. Добавьте в Git `.env.example` с безопасными примерными значениями и исключите рабочую `.env` через `.gitignore`. Покажите итог `docker compose config`, удалив реальные секреты из отчётного вывода. Объясните источник имени проекта, его приоритет и имена контейнеров, сетей и томов. Покажите различие `down` и `down -v` только на данных собственного стенда, которые можно восстановить.
