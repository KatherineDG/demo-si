from flask import Flask, render_template, request, redirect, make_response
from pymongo import MongoClient
from threading import Thread
import uuid  # Módulo para generar IDs únicos

app = Flask(__name__)
uri = "mongodb+srv://userdemo:demo123@cluster0.u3eiiyf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['demosidb']
users_collection = db['usuarios']
app.secret_key = 'your_secret_key'

# Esta variable almacenará los IDs de sesión
session_ids = {}

@app.route('/')
def index():
    username = get_username_from_session()
    if username:
        return f'¡Hola de nuevo, {username}! <a href="/home">Ir al Home</a> | <a href="/logout">Cerrar sesión</a>'
    return '¡Bienvenido! <a href="/login">Iniciar sesión</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            session_id = str(uuid.uuid4())  # Generamos un ID de sesión único
            session_ids[session_id] = username  # Almacenamos el ID de sesión junto con el nombre de usuario
            resp = make_response(redirect('/'))
            resp.set_cookie('session_id', session_id)  # Establecemos la cookie de sesión
            return resp
        else:
            return 'Credenciales incorrectas. <a href="/login">Intentar de nuevo</a>'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id in session_ids:
        del session_ids[session_id]  # Eliminamos el ID de sesión de la lista
    resp = make_response(redirect('/'))
    resp.delete_cookie('session_id')  # Eliminamos la cookie de sesión
    return resp

@app.route('/home', methods=['GET'])
def home():
    username = get_username_from_session()
    if username:
        return render_template('home.html', username=username)
    return redirect('/login')

def get_username_from_session():
    session_id = request.cookies.get('session_id')
    return session_ids.get(session_id)

def run_app(port):
    app.run(port=port)

if __name__ == '__main__':
    # Ejecutar en diferentes hilos en puertos distintos
    thread1 = Thread(target=run_app, args=(5000,))
    thread1.start()
    thread2 = Thread(target=run_app, args=(5001,))
    thread2.start()
