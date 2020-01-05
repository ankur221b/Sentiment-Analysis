from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt
import pickle
import numpy as np
from keras.preprocessing import sequence
from keras.preprocessing.text import Tokenizer 
from keras.models import load_model
from keras.backend import clear_session

app = Flask(__name__)

app.secret_key ='mysecret'
app.config['MONGO_DBNAME'] = "sentiment-db"
app.config['MONGO_URI'] = 'mongodb://ankur221b:ankur221b@sentiment-shard-00-00-c2hp2.mongodb.net:27017,sentiment-shard-00-01-c2hp2.mongodb.net:27017,sentiment-shard-00-02-c2hp2.mongodb.net:27017/test?ssl=true&replicaSet=sentiment-shard-0&authSource=admin&retryWrites=true&w=majority'
mongo = PyMongo(app)
maxlen=100

@app.route('/')
def index():
	if 'username' in session:
		#return 'You are logged in as ' + session['username'] + '''<html> <a href="/logout">logout</a> </html>'''
		return render_template('home.html',username=session['username'])

	return render_template('index.html')

def analyze(inp):
	clear_session()
	model_file = open('model.pkl','rb')
	model = pickle.load(model_file)
	tokenizer_file = open('tokenizer.pkl','rb')
	tokenizer = pickle.load(tokenizer_file)
	inp = tokenizer.texts_to_sequences([inp])
	inp = sequence.pad_sequences(inp, maxlen=maxlen)
	prediction = model.predict(inp)[0]
	model_file.close()
	tokenizer_file.close()
	clear_session()
	return prediction

@app.route('/home',methods=['POST'])
def home():
	inp, result, polarity = None,None,None
	
	inp = request.form['text']
	if inp == None:
		result = 'Invalid Input'
	else:
		prediction=analyze(inp)
		if(np.argmax(prediction) == 0):
			result = "Negative"
			polarity = "Polarity : {0:.2f}%".format(round(prediction[0]*100))

		elif (np.argmax(prediction) == 1):
			result = "Positive"
			polarity = "Polarity : {0:.2f}%".format(round(prediction[1]*100))
	
	return render_template('home.html',username=session['username'],result=result,polarity=polarity)



@app.route('/logout')
def logout():
	session.pop('username',None)
	return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name' : request.form['username']})
    error = None

    if login_user:
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['password']):
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        else:
        	error = 'Invalid Credentials'

    else:
    	error = 'Invalid Credentials'

    return render_template('index.html',error=error)


@app.route('/create', methods=['POST','GET'])
def create():
	error = None
	if request.method == 'POST':
		users = mongo.db.users
		existing_user = users.find_one({'name' : request.form['username']})
		

		if existing_user is None:
			hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'),bcrypt.gensalt())
			users.insert({'name' : request.form['username'], 'password' : hashpass})
			session['username'] = request.form['username']
			return redirect(url_for('index'))

		else:
			error = 'Username already exists'

	return render_template('create.html',error=error)
	

if __name__ == '__main__':
	app.run(debug=True)
