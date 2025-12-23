import os
from urllib.parse import quote_plus

class Config(object):
    SECRET_KEY = "87f4a864b7682e5abee526bfec36af9b408f825c4daf5dcb7d7c7012b2914aff"

    # Azure Blob Storage
    BLOB_ACCOUNT = "images19"
    BLOB_STORAGE_KEY = "pzqITF8WLL6xmxPt2GF3LTopin3khqjpHglHtddktMpZir/CgF83UpvsKd60ihPIR1BP5WkOQ0lU+AStdAv9Lg=="
    BLOB_CONTAINER = "image"
    # Azure SQL Database
    SQL_SERVER = "cmsdemodb.database.windows.net"

    SQL_DATABASE = "cms"
    SQL_USER_NAME = "cmsadmin"
    # Only quote if password exists to avoid issues
    sql_pass = "CMS4dmin"
    SQL_PASSWORD = quote_plus(sql_pass)

    # Corrected URI for ODBC Driver 18 and Azure SQL
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{SQL_USER_NAME}:{SQL_PASSWORD}"
        f"@{SQL_SERVER}:1433/{SQL_DATABASE}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes&TrustServerCertificate=no"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Azure Active Directory (MSAL)
    CLIENT_ID = "98f9ea71-0b74-443c-b28f-d79428674568"
    CLIENT_SECRET = "gjl8Q~bM9B2lMAA6Voae-y1iSQiE2s3DAbizXbuU"
    TENANT_ID = "f958e84a-92b8-439f-a62d-4f45996b6d07"

    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID or 'common'}"
    REDIRECT_PATH = "/getAToken"
    SCOPE = ["User.Read"]

    # Session configuration
    SESSION_TYPE = "filesystem"