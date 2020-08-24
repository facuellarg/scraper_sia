import flask
from flask import request, jsonify
from scheduler import get_scheduler_info
from flask_cors import CORS
app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app)
def response(data,status):
    return {'data':data,'status':status}

@app.route('/scheduler', methods=['GET'])
def scheduler():
    query_parameters = request.args
    if 'user' not in query_parameters or 'password' not in query_parameters:
        return response("bad request", 400)
    user = query_parameters['user']
    password = query_parameters['password']
    scheduler_info= None
    try:
        scheduler_info = get_scheduler_info(user, password)
    except:
         return response("No se pudo obtener la informacion, verifique usuario y contraseña",400)
    if scheduler_info is not None:
        return response(scheduler_info,200)
    else:
        return response("No se pudo obtener la informacion, verifique usuario y contraseña",400)


if __name__ == '__main__':
    app.run(debug=True)