#!/usr/bin/env python3

import os
import json
import flask
from flask import request
import psycopg
from psycopg.rows import dict_row
from elasticsearch_dsl import Search
from elasticsearch_dsl import connections
from dotenv import load_dotenv
from app import app


class MainWorker:
    def __init__(self):
        # load environment variables
        load_dotenv()
        self.__test_index = os.getenv('TEST_INDEX')
        self.__es_socket = os.getenv('ES_SOCKET')
        self.__db_name = os.getenv('DB_NAME')
        self.__db_user = os.getenv('DB_USER')
        self.__db_pwd = os.getenv('DB_PASSWORD')
        self.__db_host = os.getenv('DB_HOST')

    @staticmethod
    def response_maker(code, data, flag=False):
        """ Response constructor
        """
        if flag:
            mime = "application/json"
            resp = json.dumps({"response": data})
        else:
            mime = "text/html"
            resp = data
        return flask.Response(
            status=code,
            mimetype=mime,
            response=resp
        )

    def __db_connect(self):
        """ Creates new postgres connection

        :return: connection object
        """
        connection = psycopg.connect(
            dbname=self.__db_name,
            user=self.__db_user,
            password=self.__db_pwd,
            host=self.__db_host,
            row_factory=dict_row,
            options='-c statement_timeout=500')
        return connection

    def __es_connect(self):
        """ Creates new elasticsearch connection

        :return: connection object
        """
        connection = connections.create_connection(hosts=self.__es_socket, timeout=50)
        return connection

    def dsl_search(self, req):
        """ Main search method

        :param req: text request
        :return: dict of 20 search results as { "id" : ["created_date", "rubrics", "text"], }
        """

        id_list = []
        try:
            with self.__es_connect() as __connection:
                search_script = Search(using=__connection, index=self.__test_index).query("match_phrase", text=req)
                search_result = search_script.execute()
        except Exception as error:
            print("[INFO] Index connection error occurred: \n", error)
            return self.response_maker(500, "Index connection error. Check config.")

        for hit in search_result:
            id_list.append(hit.iD)
        if len(id_list) > 0:
            return self.db_selector(id_list)
        else:
            return self.response_maker(404, "No results")

    def db_selector(self, id_list):
        """ Selects data from DB using id list.

        Sending request to PostgreSQL DB using psycopg v.3 lib.
        Results number is limited of 20 strings.
        """

        search_script = "SELECT * FROM {} " \
                        "WHERE id = ANY(%s) " \
                        "ORDER BY created_date DESC LIMIT 20;".format(self.__test_index)
        try:
            with self.__db_connect() as db_connection:
                db_response = db_connection.execute(search_script, [id_list]).fetchall()
        except Exception as error:
            print("[ERROR] Failed to establish database connection: \n", error)
            return self.response_maker(500, "Database connection error. Check config.")
        result_dict = {}
        for num, i in enumerate(db_response):
            result_dict[num] = {'id': int(i['id']),
                                'rubrics': i['rubrics'],
                                'text': i['text'],
                                'created_date': str(i['created_date'])}
        return self.response_maker(200, result_dict, flag=True)

    def delete_via_id(self, delete_id):
        """ Deleting data from database and elastic.

        Method is used for deleting of es document and db string via id number.
        First of all it tries to make a backup from DB and then delete all the
        existing information from db and elastic index. If failed - recovers
        elastic index document and makes response "failed to delete".
        :param delete_id: id number.
        :return: string format result status.
        """
        try:
            with self.__es_connect() as __es_connection:
                with self.__db_connect() as __db_connection:
                    db_response = __db_connection.execute(f"DELETE FROM {self.__test_index} WHERE id = {delete_id}")
                    if db_response.statusmessage.endswith('1'):
                        __es_connection.delete(index=self.__test_index, id=delete_id, refresh="true")
                        __db_connection.commit()
                        return self.response_maker(200, f'id {delete_id} deleted')
                    else:
                        __db_connection.rollback()
                        return self.response_maker(410, f'id {delete_id} not found')
        except Exception as error:
            print("[ERROR] Unable to connect either database or index: \n", error)
            return self.response_maker(500, "Failed to delete")


worker = MainWorker()


@app.route('/api', methods=['GET'])
def search_request():
    return worker.dsl_search(request.form['text'])


@app.route('/api', methods=['DELETE'])
def delete_request():
    try:
        del_id = int(request.form['id'])
        return worker.delete_via_id(del_id)
    except ValueError:
        return worker.response_maker(400, "Wrong id data type. Use integer only.")
