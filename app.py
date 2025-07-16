from flask import Flask, render_template, request,jsonify, redirect, url_for, session
import pickle
import pandas as pd
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from datetime import timedelta, datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'secret'
app.permanent_session_lifetime = timedelta(days=1)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ambulance = db.Column(db.String(20))
    symptoms = db.Column(db.Text)
    prediction = db.Column(db.String(100))
    time = db.Column(db.DateTime, default=datetime.utcnow)


with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)

dataset = pd.read_csv("model/dataset.csv")
symptom_list = list(dataset.columns[:-1])

amb_pasw = "scrypt:32768:8:1$DjqpFs1fdXeT5neP$0db7d0c738c094959be0dbb52e6a0f9eb16d36d569a6f338bd6bf714c8ec37140dcf27cbb60d7b28159c12032e8a94642a0e43097c29f2e1e5a02f34b7d7baa6" # amb123
amb_no = ['HP01123', 'HP01124', 'HP01125', 'HP01126', 'HP01127']

@app.route('/', methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
        role = request.form['role']

        if role == 'ambulance':
            present_amb_no = request.form['present_amb_no']
            present_amb_pasw = request.form['present_amb_pasw']

            if present_amb_no in amb_no and check_password_hash(amb_pasw, present_amb_pasw):
                session.permanent = True
                session['user'] = present_amb_no
                session['role'] = 'ambulance'
                return redirect(url_for('amb_dashboard'))
            else:
                return render_template('login.html', error="Invalid Ambulance Credentials")

        elif role == 'doctor':
            presenet_doc_username = request.form['present_doc_username']
            present_doc_pasw = request.form['present_doc_pasw']

            if presenet_doc_username == 'doctor' and check_password_hash('scrypt:32768:8:1$mK7VSVp8DYG4RKHj$9497e7949c4e7312ede6ec1bd9dc2c0e650afe1e90d7caf1765017c07fcff7ddb1ebdfdcdd0be85292a84c12a72ccb8394174b9be583e3ad7bfa9226cbc98784',present_doc_pasw): # doc123
                session.permanent = True
                session['user'] = presenet_doc_username
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
    return render_template('disease.html', symptoms=symptom_list, prediction=prediction, user=session.get('user'))

@app.route('/get_prediction')
def get_prediction():
    if not session.get('role') or session['role'] != 'ambulance':
        return jsonify({'prediction': 'Unauthorized'}), 403

    report = Report.query.filter_by(ambulance=session['user']).first()
    return jsonify({'prediction': report.prediction if report else 'Not submitted yet'})

@app.route('/docupdate')
def doc_update():
    if session.get('role') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    reports = Report.query.order_by(Report.time.desc()).all()
    data = [
        {
            'id': r.id,
            'ambulance': r.ambulance,
            'symptoms': r.symptoms,
            'prediction': r.prediction,
            'time': r.time.strftime('%Y-%m-%d %H:%M')
        }
        for r in reports
    ]
    return jsonify(data)


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

    all_reports = Report.query.order_by(Report.time.desc()).all()
    return render_template('doc_dashboard.html', reports=all_reports)


@app.route('/logout')
def logout(): 
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)