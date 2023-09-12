import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
import os
from datetime import datetime

# Carga los datos desde el archivo CSV con encabezados de columna
datos = pd.read_csv('./books.csv')

engine = create_engine("postgresql://books_5eop_user:j3sqyOhl5I6vfimIf7n3PQjHVmEC2BPH@dpg-cjj1lpj37aks73ame8ug-a.oregon-postgres.render.com/books_5eop")
db = scoped_session(sessionmaker(bind=engine))

try:
    for index, row in datos.iterrows():
        isbn = row['isbn']
        title = row['title']
        author = row['author']
        year = int(row['year']) 

        query = text("INSERT INTO libros (isbn, titulo, autor, anio) VALUES (:isbn, :titulo, :autor, :anio)")
        db.execute(query, {"isbn": isbn, "titulo": title, "autor": author, "anio": year})
        print(query)

    db.commit()
    db.close()

except Exception as e:
    print(str(e))
    print('No sirvió')

