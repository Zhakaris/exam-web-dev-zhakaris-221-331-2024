import os

class Config:
    SECRET_KEY = 'b3baa1cb519a5651c472d1afa1b3f4e04f1adf6909dae88a4cd39adc0ddd9732'
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'std_2419_zhak_project')}:{os.environ.get('MYSQL_PASSWORD', 'zhakaris')}@{os.environ.get('MYSQL_HOST', 'std-mysql.ist.mospolytech.ru')}/{os.environ.get('MYSQL_DATABASE', 'std_2419_zhak_project')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
