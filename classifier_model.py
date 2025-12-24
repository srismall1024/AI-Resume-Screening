from sklearn.linear_model import LogisticRegression

classifier = LogisticRegression()
classifier.fit([[0.2], [0.4], [0.6], [0.8]], [0, 0, 1, 1])

def classify(score: float) -> str:
    result = classifier.predict([[score]])
    return "Accept" if result[0] == 1 else "Reject"
