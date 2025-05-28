from flaks import Flask, render_template, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os



app = Flask(__name__)
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
    
@app.route('/', methods=['GET', 'POST'])

def index():
    client          = connect_to_mongo()
    database        = []
    error_message   = None

    if client:
        try:
            #Get the database names
            database = client.list_database_names()
        except Exception as e:
            error_message = f"Error retrieving databases: {e}"
            print(error_message)
        finally:
            client.close()
    else:
        error_message = "Failed to connect to MongoDB."
    
    if request.method == 'POST':
        selected_db = request.form.get('database')
        collection_data = get_collections_data(selected_db)
        return render_template('index.html', databases=database,selected_db=selected_db ,collection_data=collection_data, error_message=error_message)
    return render_template('index.html', databases=database, error_message=error_message)

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

    if __name__ == '__main__':
        app.run(debug=True, host="0.0.0.0",port=os.getenv("PORT",5000))


        