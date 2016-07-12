from lisa_parser import ParseXML
import pyodbc
from envparse import env
from string import Template


def init_connection():
    connection = pyodbc.connect(get_connection_string())
    return connection, connection.cursor()


def get_connection_string():
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
    insert_command = Template('insert into $tableName($columns) values($values)')


    cursor.execute(insert_command.substitute(
        tableName=table_name,
        columns=', '.join(values_dict.keys()),
        values=', '.join("'" + item + "'" for item in values_dict.values())
    ))


def create_table(cursor):
    cursor.execute("CREATE TABLE [dbo].[TestResults]("
                   "[TestID] [bigint] IDENTITY(1,1) NOT NULL,"
                   "[TestLocation] [nchar](10) NOT NULL,"
                   "[TestArea] [nchar](50) NOT NULL,"
                   "[TestCaseName] [nchar](50) NOT NULL,"
                   "[TestDate] [date] NOT NULL,"
                   "[HostName] [nchar](50) NOT NULL,"
                   "[HostVersion] [nchar](50) NOT NULL,"
                   "[GuestOSType] [nchar](30) NOT NULL,"
                   "[GuestOSDistro] [nchar](50) NOT NULL,"
                   "[TestResult] [nchar](10) NOT NULL,"
                   "[KernelVersion] [nchar](30) NULL,"
                   "[IPVersion] [nchar](4) NULL,"
                   "PRIMARY KEY CLUSTERED ("
                   "[TestID] ASC"
                   ") WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON))"
                   )

