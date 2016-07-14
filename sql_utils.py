"""
Copyright (c) Cloudbase Solutions 2016
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from string import Template
from envparse import env
import pyodbc


def init_connection():
    connection = pyodbc.connect(get_connection_string())
    return connection, connection.cursor()


def get_connection_string():
    """
    Constructs the connection string necessary
    for the Azure DB using constants saved in
    config/.env
    """
    env.read_envfile('config/.env')

    connection_string = Template("Driver={$SQLDriver};"
                                 "Server=$server,$port;"
                                 "Database=$db_name;"
                                 "Uid=$db_user;"
                                 "Pwd=$db_password;"
                                 "Encrypt=$encrypt;"
                                 "TrustServerCertificate=$certificate;"
                                 "Connection Timeout=$timeout;")

    return connection_string.substitute(
        SQLDriver=env.str('Driver'),
        server=env.str('Server'),
        port=env.str('Port'),
        db_name=env.str('Database'),
        db_user=env.str('User'),
        db_password=env.str('Password'),
        encrypt=env.str('Encrypt'),
        certificate=env.str('TrustServerCertificate'),
        timeout=env.str('ConnectionTimeout')
    )


def insert_values(cursor, table_name, values_dict):
    """
    Executes an insert command on the db using the values
     provided by de value_dict in which the keys represent
     table columns and the dict values are the values to be
     inserted
    """
    insert_command = Template('insert into $tableName($columns)'
                              ' values($values)')

    cursor.execute(insert_command.substitute(
        tableName=table_name,
        columns=', '.join(values_dict.keys()),
        values=', '.join("'" + item + "'" for item in values_dict.values())
    ))
