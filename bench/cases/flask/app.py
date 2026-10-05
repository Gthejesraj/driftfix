from decimal import Decimal

from flask import Flask, Markup, escape, jsonify
from flask.json import JSONEncoder


class ShopEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


app = Flask(__name__)
app.json_encoder = ShopEncoder
STATE = {"inits": 0}


@app.before_first_request
def warm_up():
    STATE["inits"] += 1


@app.get("/price")
def price():
    return jsonify(price=Decimal("9.99"), inits=STATE["inits"])


@app.get("/greet/<name>")
def greet(name):
    return str(Markup("<b>{}</b>").format(escape(name)))
