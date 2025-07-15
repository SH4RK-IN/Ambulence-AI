from flask import Flask, render_template, request,jsonify, redirect, url_for, session
import pickle
import pandas as pd
import numpy as np
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'secret'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ambulance = db.Column(db.String(20))
    symptoms = db.Column(db.Text)
    prediction = db.Column(db.String(100))


with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)

dataset = pd.read_csv("model/dataset.csv")
symptom_list = list(dataset.columns[:-1])

ambulence_pass = "amb123"
ambulence_no = ['HP01123', 'HP01124', 'HP01125', 'HP01126', 'HP01127']

@app.route('/', methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
        role = request.form['role']

        if role == 'ambulance':
            amb_no = request.form['amb_no']
            pasw = request.form['pasw']
            if amb_no in ambulence_no and pasw == ambulence_pass:
                session['user'] = amb_no
                session['role'] = 'ambulance'
                return redirect(url_for('amb_dashboard'))
            else:
                return render_template('login.html', error="Invalid Ambulance ID or Password")

        elif role == 'doctor':
            uname = request.form['username']
            pword = request.form['password']
            if uname == 'admin' and pword == 'admin':
                session['user'] = uname
                session['role'] = 'doctor'
                return redirect(url_for('doctor'))
            else:
                return render_template('login.html', error="Invalid Doctor Credentials")

    return render_template('login.html')

@app.route('/ambulance-dashboard')
def amb_dashboard():
    if session.get('role') != 'ambulance':
        return redirect(url_for('login'))

    return render_template('amb_dashboard.html', user=session.get('user'))

@app.route('/disease', methods=['POST','GET'])
def disease():
    if not session.get('role') or session['role'] != 'ambulance':
        return redirect(url_for('login'))

    prediction = None

    if request.method == 'POST':
        selected_symptoms = request.form.get('selected_symptoms', '').split(',')
        selected_symptoms = [s for s in selected_symptoms if s]
        if selected_symptoms:
            input_vector = [1 if symptom in selected_symptoms else 0 for symptom in symptom_list]
            input_vector = np.array(input_vector).reshape(1, -1)
            prediction = model.predict(input_vector)[0]

            existing = Report.query.filter_by(ambulance=session['user']).first()
            if existing:
                existing.symptoms = ",".join(selected_symptoms)
                existing.prediction = prediction
            else:
                new_report = Report(
                    ambulance=session['user'],
                    symptoms=",".join(selected_symptoms),
                    prediction=prediction
            )
            db.session.add(new_report)


        else:
            prediction = "Please select at least one symptom."
        db.session.commit()
    return render_template('disease.html', symptoms=symptom_list, prediction=prediction)

@app.route('/get_prediction')
def get_prediction():
    if not session.get('role') or session['role'] != 'ambulance':
        return jsonify({'prediction': 'Unauthorized'}), 403

    report = Report.query.filter_by(ambulance=session['user']).first()
    return jsonify({'prediction': report.prediction if report else 'Not submitted yet'})


@app.route('/doctor-dashboard', methods=['GET', 'POST'])
def doctor():
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))

    if request.method == 'POST':
        report_id = int(request.form['id'])
        new_pred = request.form['new_disease']
        report = Report.query.get(report_id)
        if report:
            report.prediction = new_pred
            db.session.commit()

    all_reports = Report.query.all()
    return render_template('doc_dashboard.html', reports=all_reports)


@app.route('/logout')
def logout(): 
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)