import flask
from flask import request, jsonify
from scheduler import get_scheduler_info
from scheduler import get_scheduler_info_simulation
from flask_cors import CORS
from passlib.hash import sha256_crypt as sh256
import threading
import time
app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

schedulers = {}
threads = {}
def response(data,status):
    return {'data':data,'status':status}



def get_scheduler(user,password):
    while(True):
        schedule_info=None
        try:
            schedule_info = get_scheduler_info(user, password)
            # schedule_info = get_scheduler_info_simulation(user, password)
        except:
            continue
        schedulers[user]={}
        if isinstance(schedule_info,dict):
            schedulers[user]['password']=sh256.hash(password)
            schedulers[user]['schedule']=schedule_info    
        else:
            schedulers[user]['error']=schedule_info  
        break

@app.route('/scheduler', methods=['GET'])
def scheduler():
    query_parameters = request.args
    if 'user' not in query_parameters or 'password' not in query_parameters:
        return response("bad request", 403)
    user = query_parameters['user']
    password = query_parameters['password']
    if user in schedulers.keys():
        if 'error' in schedulers[user].keys():
            del schedulers[user]
            return response("No se pudo obtener la informacion, verifique usuario y contraseña",400)
        if sh256.verify(password, schedulers[user]['password']):
            return response(schedulers[user]['schedule'],200)
        else:
            return response("No se pudo obtener la informacion, verifique usuario y contraseña",400)
    if user in threads.keys():
        return response({'message':"Su peticion aun se esta procesando, por favor intente en un minuto"},102)
    else:
        threads[user]=threading.Thread(target=get_scheduler, args=(user,password))
        threads[user].start()
        return response({'message':"Su peticion se empezara a procesar, por favor intente en unos minutos"},102)


@app.route('/PendingUsers', methods=['GET'])
def queue_list():
   return {thread:True for thread in threads.keys()}




def clean_threads():
    while(True):
        list_keys = list(threads.keys())
        for thread in list_keys:
            if not threads[thread].is_alive():
                print("Reportando: Hilo del usuario ",thread,' finalizado')
                del threads[thread] 
        time.sleep(5)
t = threading.Thread(target=clean_threads)
t.daemon=True

@app.route('/', methods=['GET'])
def clean_threads_query():
    if not t.is_alive():
        t.start()
    return{"message":"Corriendo limpieza de hilos"}



if __name__ == '__main__': 
    t = threading.Thread(target=clean_threads)
    t.daemon=True
    t.start()
    app.run(debug=True)