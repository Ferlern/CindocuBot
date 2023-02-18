from src.database.create import create_tables, create_database

if __name__ == '__main__':
    create_database()
    create_tables()

    print('succes')
