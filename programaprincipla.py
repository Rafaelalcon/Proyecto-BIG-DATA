from flask import Flask, render_template, request, redirect
import requests as req
import random
import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector
import os

# Variable global
user = ""

# connectBD: conecta a la base de datos users en MySQL
def connectBD():
    db = mysql.connector.connect(
        host = "127.0.0.1",
        user = "root",
        passwd = "contraendoc"
    )
    cursor = db.cursor()
    cursor.execute("create schema if not exists users;")
    db.close()
    
    conexion = mysql.connector.connect(
        host = "127.0.0.1",
        user = "root",
        passwd = "contraendoc",
        database = "users"
    )
    return conexion

# initBD: crea una tabla en la BD users, con un registro, si está vacía
def initBD():
    bd = connectBD()
    cursor=bd.cursor()
    # Operación de creación de la tabla users (si no existe en BD)
    query="CREATE TABLE IF NOT EXISTS users(\
            user varchar(30) primary key,\
            password varchar(30),\
            name varchar(30));"
    cursor.execute(query)
    
    #Operación de creación de la tabla ranking (si no existe enn BD)
    query2 = "CREATE TABLE IF NOT EXISTS ranking(\
            user varchar(30) primary key,\
            puntuacion integer,\
            fallos integer);"
    cursor.execute(query2)
    bd.commit()
    bd.close()
    return


#Función para insertar usuario a la tabla ranking y una puntuacion inicial y los fallos a 0
def insertarPuntuacionfallosUser(user):
    bd = connectBD()
    cursor = bd.cursor()
    query = "INSERT INTO ranking (user, puntuacion, fallos) VALUES (%s, 0, 0);"
    values = (user,)
    cursor.execute(query, values)
    bd.commit()
    bd.close()
    return

#Función para obtener la puntución del jugador
def obtenerPuntuacion(user):
    bd = connectBD()
    cursor = bd.cursor()
    query = "SELECT puntuacion FROM ranking WHERE user = %s;"
    values = (user,)
    cursor.execute(query, values)
    puntuacion = cursor.fetchone()
    bd.commit()
    bd.close()
    if puntuacion is not None:
        return puntuacion[0]
    else:
        return 0

#Función para obtener la puntuacion de todos los jugadores
def ObtenerPuntuacionTotal():
    bd = connectBD()
    cursor = bd.cursor()
    query = "SELECT user, puntuacion from ranking;"
    cursor.execute(query)
    puntuaciones = cursor.fetchall()
    bd.close()
    return puntuaciones
    
#Función para actualizar la puntuación del usuario
def actualizarPuntuacion(user, nueva_puntuacion):
    bd = connectBD()
    cursor = bd.cursor()
    query = "UPDATE ranking SET puntuacion = %s WHERE user = %s;"
    values = (nueva_puntuacion, user)
    cursor.execute(query, values)
    bd.commit()
    bd.close()
    return

#Función para reiniciar la puntuación cada vez que inicie sesión
def reiniciarPuntuacion(user):
    bd = connectBD()
    cursor = bd.cursor()
    query = "UPDATE ranking SET puntuacion = 0 WHERE user = %s;"
    values = (user,)
    cursor.execute(query, values)
    bd.commit()
    bd.close()
    return 

#Función para reiniciar los fallos cada vez que inicie sesión
def reiniciarFallos(user):
    bd = connectBD()
    cursor = bd.cursor()
    query = "UPDATE ranking SET fallos = 0 WHERE user = %s;"
    values = (user,)
    cursor.execute(query, values)
    bd.commit()
    bd.close()      
    return

#Función para obtener fallos  
def obtenerFallos(user):
    bd = connectBD()
    cursor = bd.cursor()
    query = "SELECT fallos FROM ranking WHERE user = %s;"
    values = (user,)
    cursor.execute(query, values)
    fallos = cursor.fetchone()
    bd.close()
    if fallos is not None and fallos[0] is not None:
        return fallos[0]
    else:
        return 0

#Función para incrementar los fallos
def incrementarFallos(user):
    bd = connectBD()
    cursor = bd.cursor()
    query = "UPDATE ranking SET fallos = fallos + 1 WHERE user = %s;"
    values = (user,)
    cursor.execute(query, values)
    bd.commit()
    bd.close()
    return

#Función para comprobar los fallos y acabar el juego
def comprobarFinJuego(user):
    fallos = obtenerFallos(user)
    return fallos >= 3

#Función para comprobar el usuario
def checkUserSecure(user, password):
    bd = connectBD()
    cursor = bd.cursor()
    query="SELECT user, name FROM users WHERE user=%s \
        AND password = %s"
    values = (user, password)
    cursor.execute(query, values)
    userData = cursor.fetchall()
    bd.close()
    if userData == []:
        return False
    else:
        return userData[0]
    
# createUser: crea un nuevo usuario en la BD
def createUser(user,password,name):
    bd = connectBD()
    cursor = bd.cursor()
    query = "insert into users (user, password, name) values (%s,%s,%s);"
    values = (user,password,name)
    cursor.execute(query, values)
    bd.commit()
    bd.close()
    insertarPuntuacionfallosUser(user)
    return 

#Función para seleccionar una pregunta de la API
def SeleccionarPregunta():
    #Obtención de los datos de la API
    response = req.get('https://the-trivia-api.com/api/questions')
    questions = response.json()
    
    random_index = random.randint(0, len(questions) - 1)
    question = questions[random_index]
    options = question["incorrectAnswers"] + [question["correctAnswer"]]
    random.shuffle(options)
    return question["question"], options, question["correctAnswer"]

#Función para comprobar la respuesta del usuario
def comprobarResultado(respuesta, opcionCorrecta):
    return respuesta == opcionCorrecta


#Función de analisis de datos, genera un gráfico que analiza las preguntas por dificultad y las separa
def generarGrafico():
    #Obtención datos de la API
    response = req.get('https://the-trivia-api.com/api/questions')
    questions = response.json()
    #Crear un DataFrame a partir de los datos obtenidos
    df = pd.DataFrame(questions)

    #Etapa de limpieza/acondicionamiento
    #Vamos a seleccionar solo las columnas que nos interesan y renombrarlas
    df = df[['question', 'difficulty']]
    df= df.rename(columns={'question':'Pregunta', 'difficulty':'Dificultad'})

    #Etapa de análisis
    #contamos la cantidad de preguntas por dificultad y las ordenamos 
    preguntas_por_dificultad = df['Dificultad'].value_counts().sort_values()

    # Etapa de visualización
    # Vamos a generar un gráfico de barras para visualizar la distribución de dificultades
    fig, ax = plt.subplots()
    x = preguntas_por_dificultad.index
    y = preguntas_por_dificultad.values
    ax.bar(x,y,width=0.8)
    plt.xlabel('Dificultad')
    plt.ylabel('Cantidad de preguntas')
    plt.title('Distribución de preguntas por dificultad')
    
    #Guardamos la imagen 
    grafico = os.path.join(app.root_path, 'static', 'grafico.png')
    plt.savefig(grafico)
    
#PARTE PRINCIPAL
#Ruta principal de programa devolverá un html llamado home
app = Flask(__name__)
@app.route("/")
def home():
    return render_template("home.html")

#Ruta /login cuando acceda a esta ruta se ejecutará la función login y retornará el html login que tiene un formulario que 
#contiene un atributo action que es la ruta que indica a la que enviará el formulario cuando se envíe, en este caso, la ruta "/menu" con un método POST.
@app.route("/login")
def login():
    return render_template("login.html")

#Ruta /signin cuando accesa a esta ruta se ejecutará la función signin y se ejecutará la función initBD() que sirve crear 
#las tablas correspondientes (users,ranking) y retornará el html signin que tiene un formulario y que contiene un atributo 
#action que es la ruta que indica a la que enviará el formulario cuando se envíe, en este caso, la ruta "/newUser" con un método POST.
@app.route("/signin")
def signin():
    initBD()
    return render_template("signin.html")

#Ruta que acepta solicitudes GET y POST esta se encarga de que cuando enviemos el formulario de la ruta signin llame a la función 
#createUser() para crear al usuario obtenemos los parametros desde el formulario de signin, los recogemos y los pasamos a la función
#y dependiendo de si es correcta o no devolverá una cosa u otra, si newuser es False enviará a un template newUser.html que contendrá
#un control en este caso si signin es False mensaje de Signin incorrecto y en caso contrario si newuser es True
#el template será el mismo pero al ser True mostrará un mensaje de signin correcto y estará registrado.
@app.route("/newUser", methods=('GET', 'POST'))
def newUser():
    if request.method == ('POST'):
        formData = request.form
        user = formData['usuario']
        password=formData['contrasena']
        name=formData['name']
        newuser = createUser(user, password, name)
        if newuser == False:
            return render_template("newUser.html",signin=False)
        else:
            return render_template("newUser.html",signin=True)

#Ruta que controla si el usuario esta logeado o no, obtenemos mediante el form de login los datos necesarios 
#llamamos a la función checkUserSecure() para comprobar si el usuario tiene cuenta o no, si devuelve False 
#devolverá un template con el mensaje de login incorrecto y si devuelve True el usuario podrá entrar al menu.html
@app.route('/menu', methods=('GET', 'POST'))
def menu():
    global user
    if request.method == ('POST'):
        formdata = request.form
        user = formdata.get('usuario')
        password = formdata.get('contrasena')
        userData = checkUserSecure(user, password)
        reiniciarPuntuacion(user)
        reiniciarFallos(user)
        if userData == False:
            return render_template("menu.html", login=False)
        else:
            return render_template("menu.html", login = True, usuario_iniciado = user)
    else:
        reiniciarPuntuacion(user)
        reiniciarFallos(user)
        return render_template("menu.html", login=True, usuario_iniciado=user)

#Ruta que devuelve las preguntas llamando a la función SeleccionarPregunta()    
@app.route('/results', methods=('GET', 'POST'))
def results():
    global user
    question, options, correct_option = SeleccionarPregunta()
    return render_template("results.html",preguntahtml=question, options=options, correct_option=correct_option, usuario_iniciado = user)
    
#Ruta que comprueba la respuesta del usuario llamando a la función comprobarResultado() pasando por parámetro la respuesta del usuario
#y la respuesta correcta obteniendo los dos valores desde el form de html results si la respuesta es correcta sumará 10 puntos
#y devolverá un template con un mensaje de respuesta correcta y si falla un template con mensaje de incorrecto y se le sumará un fallo
#también se comprueba si tiene más de 3 fallos para acabar el juego si tiene más será redirigido a una ruta '/finJuego' que devolverá
#un html con un mensaje de GameOver y el ranking de las puntuaciones
@app.route('/checkResultado', methods=['POST'])
def checkResultado():
    global user
    respuesta_usuario = request.form['option']
    opcion_correcta = request.form['opcion_correcta']
    resultado = comprobarResultado(respuesta_usuario, opcion_correcta)
    user = request.form['usuario_iniciado']
    if resultado == True:
        puntuacion_actual = obtenerPuntuacion(user)
        nueva_puntuacion = puntuacion_actual + 10
        actualizarPuntuacion(user, nueva_puntuacion)
    else:
        incrementarFallos(user)
        if comprobarFinJuego(user):
            return redirect('/finJuego')
    return render_template("resultado.html", respuesta=resultado, opcion=opcion_correcta, usuario_iniciado = user)

#Ruta que devuelve html finJuego y enseña el ranking con las mayores puntuaciones de los jugadores
@app.route('/finJuego')
def finJuego():
    puntuaciones = ObtenerPuntuacionTotal()
    return render_template("finJuego.html", puntuaciones=puntuaciones)

#Ruta que devuele el gráfico en un html obtenido de la función generarGrafico() 
@app.route('/grafico')
def grafico():
    generarGrafico()
    return render_template('grafico.html')

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(host='localhost', port=5000, debug=True)