import os
import requests

from flask import Flask, session, render_template, redirect, request, url_for
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


@app.route("/")
def index():
    return redirect(url_for('login'))



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            usuario = request.form['username']
            password = request.form['password']
            
            query = text('SELECT contrasena FROM usuarios WHERE nombre = :username')
            result = db.execute(query, {'username': usuario}).fetchone()
     
            print(result[0], 'password')

            if result is not None and check_password_hash(result[0], password):
                # Aquí debes agregar la autenticación exitosa
                return redirect(url_for('home'))  
            else:
                return "Credenciales inválidas"  

        except Exception as a:
            print(str(a))  # Manejo de excepciones temporal
            return "Error en el servidor" 

    else:
        return render_template('login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    """ registro de usuarios """
    if request.method == 'POST':
        if request.form.get('password')  != request.form.get('confirm_password'):
            return 'Las contrasenias no coinciden'
        
        try:
            usuario = request.form['username']
            password = request.form['password']
            print(usuario, password)
            query = text("INSERT INTO usuarios(nombre, contrasena) VALUES (:username, :hash)")
            db.execute(query, {"username":usuario , "hash":generate_password_hash(password)})
            db.commit()
            return redirect(url_for('login.html')) 
        except Exception(e):
            print(str(e))
            return 'El usuario ya existe'
    else:
        return render_template('register.html')

isbn='080213825X'
response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()

libro = None
titulo = ""
autores = []
descripcion = ""

# Manejo de errores y obtención de datos
if 'items' in response:
    primer_libro = response['items'][0]['volumeInfo']
    if 'title' in primer_libro:
        titulo = primer_libro['title']
    if 'authors' in primer_libro:
        autores = primer_libro['authors']
    if 'description' in primer_libro:
        descripcion = primer_libro['description']
        
@app.route("/home")
def home():
    # Aquí debes implementar la lógica para la página de inicio
    books = {'titulo': titulo, 'autores': autores, 'descripcion': descripcion}
    return render_template('home.html', book= books)