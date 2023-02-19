from src.database.create import recreate_tables, create_database

if __name__ == '__main__':
    create_database()
    recreate_tables()

    print('succes')
