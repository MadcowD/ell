from flask import Flask

import ell2a

@ell2a.simple(model="gpt-4o-mini")
def hello(name: str):
    """You are a helpful assistant"""
    return f"Write a welcome message for {name}."

app = Flask(__name__)


@app.route('/')
def home():
    return hello("world")

if __name__ == '__main__':
    app.run(debug=True)
