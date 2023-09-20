import os
import requests

from flask import Flask, session, render_template, redirect, request, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

class BOOK:
    def __init__(self, isbn, titulo, autor, year, idlibro, imagen):
        self.isbn = isbn
        self.titulo = titulo
        self.autor = autor
        self.year = year
        self.idlibro = idlibro
        self.imagen = imagen
        

    def formatear_autor(self):
        longitud = len(self.autor)
        if longitud > 2:
            del self.autor[2:]
        self.autor = ", ".join(self.autor)
        if longitud > 2:
            self.autor = self.autor + " and more"

class Resenia:
    def __init__(self, idresenia, idusuario, resenian, puntaje, idlibro, nombre):
        self.idresenia = idresenia
        self.idusuario = idusuario
        self.resenian = resenian
        self.puntaje = puntaje
        self.idlibro = idlibro
        self.nombre = nombre

@app.route("/")
def index():
    return redirect('/login')

@app.route("/login", methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        usuario = request.form['username']
        password = request.form['password']
        if not usuario:
            flash("Debe ingrear un usuario")
            return render_template('login.html')
        try:
            query = text('SELECT idusuario, nombre,contrasena FROM usuarios WHERE nombre = :username')
            result = db.execute(query, {'username': usuario}).fetchone()
            print("entro")
            print(result[1], 'password')
            idusuario, nombre,contrasena = result
     
            if result is not None and check_password_hash(result[2], password):
                session['user_id'] = idusuario
                session['nombre'] = nombre
                print("va al home")
                return redirect(url_for('home'))
            else:
                flash("Credenciales invalidas")
                return render_template('login.html') 

        except Exception as a:
            flash("Credenciales invalidas")
            return render_template('login.html') 
    else:
        return render_template('login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    """ registro de usuarios """
    if request.method == 'POST':
        usuario = request.form['username']
        password = request.form['password']
        if  not usuario:
            flash("Ingrese un usuario")
            return render_template('register.html')

        if  not password :
            flash("Debe ingresar una contraseña")
            return render_template('register.html')

        if password  != request.form.get('confirm_password'):
            flash("Las contraseñas no coinciden!")
            return render_template('register.html')
        
        try:
           
            print(usuario, password)
            query = text("INSERT INTO usuarios(nombre, contrasena) VALUES (:username, :hash)")
            db.execute(query, {"username":usuario , "hash":generate_password_hash(password)})
            db.commit()
            flash("Registered!")
            return redirect('/login') 
        except Exception as e:
            print(str(e))
            return 'El usuario ya existe'
    else:
        return render_template('register.html')

# isbn='080213825X'
# response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()

# libro = None
# titulo = ""
# autores = ""
# descripcion = ""

# # Manejo de errores y obtención de datos
# if 'items' in response:
#     primer_libro = response['items'][0]['imageLinks']
#     if 'thumbnail' in primer_libro:
#         imagen_libro = primer_libro['thumbnail']
        
@app.route("/home", methods = ["GET", "POST"])
def home():

    if 'user_id' in session:
        if request.method == "POST":
            print("entro al if")
            busqueda = request.form.get("busqueda")
            input = f"%{busqueda}%".lower()
            print(input)
            query = text("SELECT * FROM libros WHERE LOWER(isbn) like :isbn OR LOWER(titulo) LIKE :titulo OR LOWER(autor) LIKE :autor OR year LIKE :year")
            resultado = db.execute(query, {"isbn":input,"titulo":input,"autor":input,"year":input}).fetchall()
        
            libros = [] 
            print("esta afuera del for")
            for idlibro, isbn, titulo, autor, anio, year in resultado:
                print("Id libro: " + str(idlibro) + " el isbn: " + isbn + " El titulo es: " + titulo)
                response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:" + isbn).json()
                
                imagen_libro = "https://th.bing.com/th/id/OIP.vDf037OKUo0H03weRxdWuAHaHa?pid=ImgDet&rs=1"  # Establece la imagen por defecto si np tiene
                
                libro = {}  
                if 'items' in response:
                    for item in response['items']:
                        libro = item.get("volumeInfo", {})
                        if 'imageLinks' in libro:
                            imagen_libro = libro['imageLinks'].get('thumbnail', None)
                            break  # Sal del bucle cuando encuentres una imagen válida
                
                if 'description' in libro:
                    descripcion_libro = libro['description']
                
                nuevo_libro = BOOK(isbn, titulo, autor.split(', '), year, idlibro, imagen_libro)
                nuevo_libro.formatear_autor()
                libros.append(nuevo_libro)
            return render_template('home.html', libros = libros, nombre= session['nombre'], requet =request.method)
        else:
            print("si")
            return render_template("home.html",nombre= session['nombre'])
    else:
        flash("Debe iniciar sesion")
        return render_template('login.html')
        

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/infoLibro/<int:idlibro>")
def infoLibro(idlibro):
    if 'user_id' in session:
        query=text("SELECT * FROM libros WHERE idlibro = :idlibro")
        resultado = db.execute(query, {"idlibro":idlibro}).fetchone()

        idlibro,isbn, titulo, autor, anio, year = resultado

        print(idlibro,isbn, titulo, autor, anio, year)
        
        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:" + isbn).json()
        imagen_libro = "https://th.bing.com/th/id/OIP.vDf037OKUo0H03weRxdWuAHaHa?pid=ImgDet&rs=1"
        libro = {}    
        if 'items' in response:
            for item in response['items']:
                libro = item.get("volumeInfo", {})
                if 'imageLinks' in libro:
                    imagen_libro = libro['imageLinks'].get('thumbnail', None)
                    break  # Sale del bucle cuando encuentra una imagen válida
        
        if 'description' in libro:
            descripcion_libro = libro['description']
        cur_book = BOOK(isbn, titulo, autor, year, idlibro,imagen_libro)
        query = text("SELECT r.IdResenia, r.idUsuario, r.resenian, r.puntaje, r.idlibro, u.nombre FROM resenias r INNER JOIN libros l ON l.idlibro = r.idlibro INNER JOIN usuarios u on r.idusuario = u.idusuario WHERE l.idlibro = :idlibro")

        resenias = db.execute(query, {"idlibro" : idlibro}).fetchall()
        comentarios=[]

        puntaje = resenias
        print("asdasd")
        print(puntaje)
        print("asdasd")
        print(resenias)
        print("asdasd")
        for IdResenia, idUsuario, resenian, puntaje, idlibro, nombre in resenias:
            print( IdResenia, idUsuario, resenian, puntaje, idlibro)
            resenia_nueva = Resenia(IdResenia, idUsuario, resenian, puntaje, idlibro, nombre)
            comentarios.append(resenia_nueva)

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"isbns": cur_book.isbn})
        print (res)
        print("si llego")
        if res.status_code != 200:
            raise Exception("ERROR: No se pudo acceder a la API.")
        reseniasLibro = res.json()
        promedioResenia = float(reseniasLibro['books'][0]['average_rating'])
        contadorPuntos = float(reseniasLibro['books'][0]['work_ratings_count'])
        print("antes del render")
        return render_template("infoLibro.html", book = cur_book, comments = comentarios, promedioResenia = promedioResenia, contadorPuntos = contadorPuntos, nombre= session['nombre'])
    else:
        flash("Debe iniciar sesion")
        return render_template('login.html')

@app.route("/resenia", methods=["POST"])
def post_comment():
    if request.method=="POST":
        idUsuario = session["user_id"]
        idlibro = request.form.get("book_id")
        resenian=request.form.get("book_comment")
        puntaje = float(request.form.get("rating")) if request.form.get("rating") is not None else 0

        query = text("SELECT * FROM resenias WHERE idUsuario = :idUsuario AND idlibro = :idlibro")
        check = db.execute(query,{"idUsuario":idUsuario, "idlibro":idlibro}).fetchone()
        if check==None:
            if puntaje != 0:
                query = text("INSERT INTO resenias (idUsuario, resenian, puntaje, idlibro) VALUES (:idUsuario, :resenian, :puntaje, :idlibro)")
                db.execute(query,{"idUsuario":idUsuario, "resenian":resenian, "puntaje":puntaje, "idlibro":idlibro})
                db.commit()
            else:
                flash("Debe dar una puntuacion")
        else:
            flash("Solo puede hacer una reseña por libro")
        
        return redirect(url_for("infoLibro", idlibro = idlibro), "303")


@app.route("/api/<string:Pisbn>")
def externalapi(Pisbn):  
    P_isbn=f"%{Pisbn}%".lower()
    query = text("SELECT * FROM libros WHERE LOWER(isbn) LIKE :isbn")
    res = db.execute(query,{"isbn":P_isbn}).fetchone()
    if res is None:
        return jsonify({
        "Error":404,
        "Mensaje de error": f"No se encontro el libro con ISBN: {Pisbn}"
        }), 404

   
    
    idlibro, isbn, titulo, autor, anio, year = res
    libro =  BOOK(isbn, titulo, autor, year, idlibro, " ")
    
    res2 = requests.get("https://www.goodreads.com/book/review_counts.json", params={"isbns": libro.isbn})
    reseniasLibro = res2.json()
    promedioResenia = float(reseniasLibro['books'][0]['average_rating'])
    contadorPuntos = float(reseniasLibro['books'][0]['work_ratings_count'])
    result = {
    "Title": libro.titulo,
    "author": libro.autor,
    "year": libro.year,
    "isbn": libro.isbn,
    "review_count": contadorPuntos,
    "average_score": promedioResenia
    }
    return jsonify(result)       