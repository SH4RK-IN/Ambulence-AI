from flask import Flask, render_template, request
import pickle
import pandas as pd
import numpy as np

app = Flask(__name__)

with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)

dataset = pd.read_csv("model/dataset.csv")
symptom_list = list(dataset.columns[:-1])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/disease', methods=['POST','GET'])
def disease():
    prediction = None

    if request.method == 'POST':
        selected_symptoms = request.form.get('selected_symptoms', '').split(',')
        selected_symptoms = [s for s in selected_symptoms if s]
        if selected_symptoms:
            input_vector = [1 if symptom in selected_symptoms else 0 for symptom in symptom_list]
            input_vector = np.array(input_vector).reshape(1, -1)
            prediction = model.predict(input_vector)[0]
        else:
            prediction = "Please select at least one symptom."

    return render_template('disease.html', symptoms=symptom_list, prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)