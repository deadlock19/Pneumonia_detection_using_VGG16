from flask import Flask,render_template,redirect,request,send_from_directory, url_for,session
from tensorflow import keras
from keras.models import load_model
from flask_sqlalchemy import SQLAlchemy
import os
from PIL import Image
import numpy as np
from werkzeug.utils import secure_filename

model_file = "model.h5"
model = load_model(model_file)

app = Flask(__name__, template_folder='templates')
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password

def makePredictions(path):
  '''
  Method to predict if the image uploaed is healthy or pneumonic
  '''
  img = Image.open(path) # we open the image
  img_d = img.resize((224,224))
  # we resize the image for the model
  rgbimg=None
  #We check if image is RGB or not
  if len(np.array(img_d).shape)<3:
    rgbimg = Image.new("RGB", img_d.size)
    rgbimg.paste(img_d)
  else:
      rgbimg = img_d
  rgbimg = np.array(rgbimg,dtype=np.float64)
  rgbimg = rgbimg.reshape((1,224,224,3))
  predictions = model.predict(rgbimg)
  a = int(np.argmax(predictions))
  if a==1:
    a = "pneumonic"
  else:
    a = "healthy"
  return a

######################login##################################

@app.route('/enter/', methods=['GET','POST'])
def index2():
    if session.get('logged_in'):
        return render_template('home2.html')
    else:
        return render_template('index2.html', message="Hello! Let's get rid of PNEUMONIA")

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db.session.add(User(username=request.form['username'], password=request.form['password']))
            db.session.commit()
            return redirect(url_for('login'))
        except:
            return render_template('index2.html', message="User Already Exists")
    else:
        return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        u = request.form['username']
        p = request.form['password']
        data = User.query.filter_by(username=u, password=p).first()
        if data is not None:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return render_template('index2.html', message="Incorrect Details")


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('index2'))

##############################################################

@app.route('/',methods=['GET','POST'])
def home():
    if request.method=='POST':
        if 'img' not in request.files:
            return render_template('home.html',filename="unnamed.png",message="Please upload an file")
        f = request.files['img'] 
        filename = secure_filename(f.filename) 
        if f.filename=='':
            return render_template('home.html',filename="unnamed.png",message="No file selected")
        if not ('jpeg' in f.filename or 'png' in f.filename or 'jpg' in f.filename):
            return render_template('home.html',filename="unnamed.png",message="Please upload an image with .png or .jpg/.jpeg extension")
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        if len(files)==1:
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        else:
            files.remove("unnamed.png")
            file_ = files[0]
            #os.remove(app.config['UPLOAD_FOLDER']+'/'+file_)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            
        predictions = makePredictions(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        return render_template('home.html',filename=f.filename,message=predictions,show=True)
    return render_template('home.html')

if __name__=="__main__":
    app.secret_key = "ThisIsNotASecret:p"
    db.create_all()
    app.run(debug=True)