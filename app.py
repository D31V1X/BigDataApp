from flask import Flask, render_template, request, session, redirect, url_for
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os


#Para llevar el secreto de la app desde las variables de entorno recomendada para seguridad
app = Flask(__name__)
app.secret_key = os.environ.get('secret_key')
if not app.secret_key:
    app.secret_key = "ucentraldeivid"





mongo_uri = os.environ.get('MONGO_URI')


if not mongo_uri:
    uri = 'mongodb+srv://DbCentral:DbCentral@cluster0.gqd4gxq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
    mongo_uri = uri


def connect_to_mongo():
    try:
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        print("Connected to MongoDB")
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None
    

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        mensaje = request.form.get('mensaje')
        client = connect_to_mongo()
        if client:
            db = client['administracion']
            collection = db['contactos']
            try:
                collection.insert_one({
                    'nombre': nombre,
                    'email': email,
                    'mensaje': mensaje
                })
                client.close()
                return render_template('contacto.html', success=True)
            except Exception as e:
                print(f"Error al insertar el contacto: {e}")
                client.close()
                return render_template('contacto.html', error=True)
        else:
            return render_template('contacto.html', error=True)
    # Para GET (cuando solo accedes a la página sin enviar datos)
    return render_template('contacto.html')
        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            client = connect_to_mongo()
            if client:
                db = client['administracion']
                seguridad_collection = db['seguridad']

                username = request.form.get('username')
                password = request.form.get('password')

                print("Credenciales recibidas:", username, password)

                user = seguridad_collection.find_one({'usuario': username, 'pass': password})
                print("Resultado búsqueda:", user)

                if user:
                    session['username'] = username
                    print("Usuario autenticado:", session['username'])
                    return redirect(url_for('gestion_mongodb'))
                else:
                    error_message = "Usuario o contraseña incorrectos."
                    return render_template('login.html', error_message=error_message)
            else:
                error_message = "No se tiene conexión a la base de datos."
                return render_template('login.html', error_message=error_message)
        except Exception as e:
            print("❌ Error en login:", e)
            return f"Error interno: {str(e)}"
    else:
        return render_template('login.html')
            

@app.route('/gestionMongoDB', methods=['GET', 'POST'])
def gestion_mongodb():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        client = connect_to_mongo()

        # Obtener lista de bases de datos (excepto las internas)
        databases = client.list_database_names()
        system_dbs = ['admin', 'local', 'config']
        databases = [db for db in databases if db not in system_dbs]

        # Manejo de base seleccionada desde POST o GET
        selected_db = request.form.get('database') if request.method == 'POST' else request.args.get('database')
        collections_data = []

        if selected_db:
            db = client[selected_db]
            collections = db.list_collection_names()
            for index, collection_name in enumerate(collections, 1):
                count = db[collection_name].count_documents({})
                collections_data.append({
                    'index': index,
                    'name': collection_name,
                    'count': count
                })

        return render_template('gestionmongoDB.html',
                               databases=databases,
                               selected_db=selected_db,
                               collection_data=collections_data,
                               error_message=None,
                               username=session['username'])
    
    except Exception as e:
        print("❌ Error en gestion_mongodb:", e)
        return render_template('gestionmongoDB.html',
                               databases=[],
                               selected_db=None,
                               collection_data=[],
                               error_message=f'Error al conectar con MongoDB: {str(e)}',
                               username=session.get('username', ''))








def get_collections_data(selected_db):
    client = connect_to_mongo()
    collection_data = []
    
    if client and selected_db:
        db = client[selected_db]
        try:
            collections = db.list_collection_names()
            for index, collection_name in enumerate(collections):
                count = db[collection_name].count_documents({})
                collection_data.append({
                    'name': collection_name,
                    'count': count,
                    'index': index+1
                })
        
        except Exception as e:
            print(f"Error al obtener la lista de colecciones de la base {selected_db}: {e}")
        finally:
            client.close()
    return collection_data

def get_registros_data(selected_db, collection_name, limit=10):
    client = connect_to_mongo()
    registros_data = []
    
    if client and selected_db and collection_name:
        db = client[selected_db]
        try:
            collection = db[collection_name]
            registros_data = list(collection.find())
        except Exception as e:
            print(f"Error al obtener los registros de la colección {collection_name} en la base {selected_db}: {e}")
        finally:
            client.close()
    
    return registros_data

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port=os.getenv("PORT",5000))

if __name__ == '__main__':
    app.run(debug=True)
        