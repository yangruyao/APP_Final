from flask import render_template, Blueprint

app=Blueprint('app',__name__)

@app.route('/app')
def app_home():
  return render_template('app.html', title='Mapa de España')