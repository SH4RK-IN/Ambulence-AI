from sklearn.naive_bayes import BernoulliNB
import pandas as pd
import pickle

dataset = pd.read_csv("model/dataset.csv")
X = dataset.iloc[:, :-1]
y = dataset.iloc[:, -1]

model = BernoulliNB()

model.fit(X, y)

with open("model/model.pkl", "wb") as f:
    pickle.dump(model, f)