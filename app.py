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
        client = connect_to_mongo()
        if client:
            db = client['administracion']
            seguridad_collection = db['seguridad']

            username = request.form.get('username')
            password = request.form.get('password')

            # Verificar credenciales
            user = seguridad_collection.find_one({'usuario': username, 'pass': password})

            if user:
                session['username'] = username
                # No guardes la contraseña en sesión
                return redirect(url_for('gestion_mongodb'))
            else:
                error_message = "Usuario o contraseña incorrectos."
                return render_template('login.html', error_message=error_message)
        else:
            error_message = "No se tiene conexión a la base de datos."
            return render_template('login.html', error_message=error_message)
    else:
        # GET: mostrar el formulario sin errores
        return render_template('login.html')
            
            

@app.route('/gestionMongoDB', methods=['GET', 'POST'])
def gestion_mongodb():
    if 'username' not in session:
        return redirect(url_for('login'))

    error_message = None
    selected_db = None
    collection_data = []
    registros = []
    database = []

    client = connect_to_mongo()
    if client:
        try:
            database = client.list_database_names()

            if request.method == 'POST':
                selected_db = request.form.get('database')
                collection_name = request.form.get('collection')
                try:
                    limit = int(request.form.get('limit', 10))
                except ValueError:
                    limit = 10

                collection_data = get_collections_data(selected_db)

                if collection_name:
                    registros = get_registros_data(selected_db, collection_name, limit)
        except Exception as e:
            error_message = f"Error retrieving data: {e}"
            print(error_message)
        finally:
            client.close()
    else:
        error_message = "Failed to connect to MongoDB."

    return render_template('gestionmongoDB.html',
                           databases=database,
                           selected_db=selected_db,
                           collection_data=collection_data,
                           registros=registros,
                           error_message=error_message)



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


        