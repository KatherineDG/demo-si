from flask import Flask, render_template, request, redirect, make_response, url_for
from pymongo import MongoClient
from threading import Thread
import uuid  # Módulo para generar IDs únicos

app = Flask(__name__)
uri = "mongodb+srv://userdemo:demo123@cluster0.u3eiiyf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['demosidb']
users_collection = db['usuarios']
app.secret_key = 'your_secret_key'


app.static_folder = 'static' 


# Esta variable almacenará los IDs de sesión
session_ids = {}

@app.route('/')
def index():
    username = get_username_from_session()
    return render_template('index.html', username=username)

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



@app.route('/perfil')
def perfil():
    username = get_username_from_session()
    if username:
        user = users_collection.find_one({'username': username})
        if user:
            perfil_usuario = {
                'nombre': user.get('username', 'Nombre no proporcionado'),
                'direccion': user.get('direccion', 'Dirección no proporcionada'),
                'telefono': user.get('telefono', 'Teléfono no proporcionado')
            }
            return render_template('perfil.html', perfil=perfil_usuario)
        else:
            return 'Usuario no encontrado'
    else:
        return redirect('/login')


@app.route('/cuenta')
def cuenta_billetera():
    username = get_username_from_session()
    if username:
        user = users_collection.find_one({'username': username})
        if user:
            cuenta = {
                'username': user['username'],
                'nrotarjeta': user['nrotarjeta'],
                'clavetarjeta': user['clavetarjeta'],
                'nombretarjeta': user['nombretarjeta'],
                'vencimientotarjeta': user['vencimientotarjeta'],
                'saldo': user['saldo'],
                'transacciones': user.get('transacciones', [])
            }
            return render_template('cuenta.html', cuenta=cuenta)
        else:
            return 'Usuario no encontrado'
    else:
        return redirect('/login')


@app.route('/procesar-transaccion', methods=['POST'])
def procesar_transaccion():
    nombre = request.form['nombre']
    monto = float(request.form['monto'])
     # Obtener el nombre de usuario de la sesión
    username = get_username_from_session()
    if username:
        # Buscar el usuario en la base de datos
        user = users_collection.find_one({'username': username})
        if user:
            # Verificar si hay saldo suficiente para la transacción
            saldo_actual = user.get('saldo', 0)
            if saldo_actual >= monto:
                # Actualizar el saldo en la base de datos
                nuevo_saldo = saldo_actual - monto
                users_collection.update_one(
                    {'username': username},
                    {'$set': {'saldo': nuevo_saldo}}
                )
            # Crear la nueva transacción en el formato especificado
            nueva_transaccion = f"${monto} {nombre}"
            # Actualizar la lista de transacciones del usuario
            users_collection.update_one(
                {'username': username},
                {'$push': {'transacciones': nueva_transaccion}}
            )
            
            return redirect('/cuenta')
        else:
            return 'Usuario no encontrado'
    else:
        return redirect('/login')
    

@app.route('/eliminar-transaccion', methods=['DELETE'])
def eliminar_transaccion():
    # Suponiendo que get_username_from_session() es una función que obtiene el nombre de usuario de la sesión
    username = get_username_from_session()
    transaccion = request.json.get('transaccion')
    print(transaccion)

    if not username:
        return redirect('/login')
    
    # Buscar el usuario en la base de datos
    user = users_collection.find_one({'username': username})
    if not user:
        return 'Usuario no encontrado', 404
    
    if transaccion:
        # Eliminar la transacción de la lista de transacciones del usuario en la base de datos
        result = users_collection.update_one(
            {'username': username},
            {'$pull': {'transacciones': transaccion}}
        )
        
        if result.modified_count == 0:
            return 'Transacción no encontrada', 404
    
    # Redirigir a la cuenta del usuario después de eliminar la transacción
    return redirect('/cuenta')




def run_app(port):
    app.run(port=port)

if __name__ == '__main__':
    # Ejecutar en diferentes hilos en puertos distintos
    thread1 = Thread(target=run_app, args=(5000,))
    thread1.start()
    thread2 = Thread(target=run_app, args=(5001,))
    thread2.start()
