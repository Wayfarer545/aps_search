# aps_search microservice  
  
Hi there. Here is my homework.  
Service developed using flask, psycopg (v.3) as a Postgres ORM and elasticsearch_dsl as an official  
ES connection module. This works in Docker container and uses data from PostgreSQL,  
makes an index in Elasticsearch and handles GET and DELETE http requests.  
  
### Get started
First of all, you have to get running elasticsearch server, postgres db and table with apropriate data.  
Database structure should include following columns: id (PK), rubrics, text, created_data.  
Got it?  
Ok, now you are ready to start container.  
  
The best way is to use Docker-compose.  
Example of docker-compose.yml:
```yml
version: '3.6'
services:
  APS_search:
    image: wayfarer737/aps_search:latest
    container_name: aps_search
    restart: always
    ports:
      - "9900:9900"
    environment:
      BIND: "192.168.0.10:9900"
      ## DATABASE CONNECTION
      DB_HOST: "192.168.1.2"
      DB_NAME: "default_db"
      DB_USER: "user"
      DB_PASSWORD: "password"
      ## ELASTICSEARCH CONNECTION
      ES_SOCKET: "192.168.1.3:9200"
      TEST_INDEX: "postgres table name"
networks:
  default:
    external:
      name: some_network
```
Docker image "wayfarer737/aps_search:latest" is based on "tiangolo/meinheld-gunicorn-flask:latest" one.  
Basic image includes python3.8, gunicorn 20.1.0 and meinheld wsgi as worker of gunicorn.  
It also provides flask, but had been replaced with a 2.1.2 version during an image build (and works normal).  
All you need is to specify environment variables, providing elasticsearch server and postgres connection, and define your own networking.  
  
**IMPORTANT**. Real postgres table name should be specifyed as a TEST_INDEX variable.   

### How to use  
You can find matching records (maximum 20 pcs.) or delete record by id from database.  
Both GET and DELETE requests should include apropriate request body.  
For search:  
```python
import json
import requests

url = "http://192.168.0.10:9900/api"
payload={'text': 'соли-спайсы'}

search_response = requests.request("GET", url, data=payload)
delete_response = requests.request("DELETE", url, data={"id": 973})


print(search_response.json())
print(delete_response)

```
The successful search result is in JSON format and looks like that:  
  
```json
{
    "response": {
        "0": {
            "id": 973,
            "rubrics": "['VK-1603736028819866', 'VK-57689043503', 'VK-81354963712']",
            "text": "Специалисты каждому вручили буклеты «Профилактика туберкулеза», «Подростковый суицид», «НЕТ спайсам»",
            "created_date": "2019-04-01 10:14:08"
        }
    }
}
```
Delete and empty/incomple search responses have a text/html type and payload is the operation status.

```
id 973 deleted
```



