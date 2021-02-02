import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from .const import (
    AUTH0_DOMAIN,
    ALGORITHM,
    API_AUDIENCE,
    Err_Unauth,
    Err_badrequest,
    Err_server,
    Err_unavailable,
    Err_Notfound,
    Err_NotAllowed,
    Err_NotProcessed
)

app = Flask(__name__)
setup_db(app)
# Set our app Cors based on previous course Flask CORS
#CORS(app, resources={r"/coffe/*": {"origins": "*"}})

# @app.after_request
# def after_request(response):
#    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
#    response.headers.add("Access-Control-Allow-Methods", "GET, PUT, PATCH, POST, DELETE, OPTIONS")
#    response.headers.add("Access-Control-Allow-Credentials", "true")
#    return response

# Applying Review
CORS(app)
'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
# Drinks endpoint


@app.route("/coffe/drinks")
def getdrinks():
    try:
        # lets get our drinks from our database
        drinklist = Drink.query.order_by(Drink.title).all()
        drinksarray = []
        for drinkitem in drinklist:
            # the frontend is excpecting a short format
            drinksarray.append(drinkitem.short())

        print(drinksarray)
        return jsonify({
            "drinks": drinksarray,
            "success": True
        })

    except Exception as E:
        print(E)
        abort(Err_Notfound)

# Drink Details endpoint
# we need to pass an pyld parameter
# it has no usage in the function
# but our requires_auth_decorator
# in auth.py will return it as payload


@app.route("/coffe/drinks-detail")
@requires_auth(permission='get:drinks-detail')
def getdrinkdetails(jwt_payload):  # apply review more effecit parameter payload name
    try:
        # lets get our drinks from our database
        drinklist = Drink.query.order_by(Drink.title).all()
        drinksarray = []
        for drinkitem in drinklist:
            # the frontend is excpecting a long format
            drinksarray.append(drinkitem.long())

        print(drinksarray)
        return jsonify({
            "drinks": drinksarray,
            "success": True
        })

    except Exception as E:
        print(E)
        abort(Err_Notfound)


# Create a new Drink
@app.route("/coffe/drinks", methods=["POST"])
@requires_auth(permission='post:drinks')
def AddNewDrink(jwt_payload):
    # get our json data
    jsondata = request.get_json()
    if not jsondata:
        abort(Err_Unauth)
    # set our new drink data into variables
    # or return None if the key not included
    NewdrinkTitle = jsondata.get('title', None)
    Newdrinkrecipe = jsondata.get('recipe', None)
    if NewdrinkTitle is None:
        abort(Err_Unauth)

    if Newdrinkrecipe is None:
        abort(Err_Unauth)
    # if everything is fine,
    # then lets Encode our drinkrecipe as string,
    # to be suitable for our database recipe column
    # we will use json.dumps as the following refrence
    # https://docs.python.org/3/library/json.html
    Newdrinkrecipe = json.dumps(Newdrinkrecipe)
    # now lets try to attempt to insert
    # the drink to our database
    try:
        AddDrink_Q = Drink(title=NewdrinkTitle, recipe=Newdrinkrecipe)
        AddDrink_Q.insert()
        CreatedDrink = [AddDrink_Q.long()]
        # if every thing is fine
        # then return the Created drink with success true
        return jsonify({
            "drinks": CreatedDrink,
            "success": True
        })
    except Exception as E:
        print(E)
        abort(Err_NotProcessed)


# Edit a drink data
@app.route("/coffe/drinks/<int:drinkid>", methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def ChangeDrinkdata(jwt_payload, drinkid):
    # lets get the dring by id
    # this will return none if there is no drink Found
    # with that drinkid
    GetDrinkdata = Drink.query.filter(Drink.id == drinkid).one_or_none()
    # if we did not find a drink then abort with 404
    if GetDrinkdata is None:
        abort(Err_Notfound)
    # otherwise lets read our data to update
    jsondata = request.get_json()
    # if we dont have json data then abort 401
    if not jsondata:
        abort(Err_Unauth)
    # lets set our data in variable to use them
    # or return None if the key not included
    drinktitle = jsondata.get('title', None)
    drinkrecipe = jsondata.get('recipe', None)
    # if we have None then we did not find the keys
    # then abort with 401
    if drinktitle is None:
        abort(Err_Unauth)

    if drinkrecipe is None:
        abort(Err_Unauth)

    # otherwise lets go ahead and update
    # we will use json.dumps as the following refrence
    # https://docs.python.org/3/library/json.html
    drinkrecipe = json.dumps(drinkrecipe)
    # now lets try to attempt to Update
    # the drink to our database
    try:
        GetDrinkdata.title = drinktitle
        GetDrinkdata.recipe = drinkrecipe
        GetDrinkdata.update()
        UpdatedDrink = [GetDrinkdata.long()]

        return jsonify({
            "drinks": UpdatedDrink,
            "success": True
        })

    except Exception as E:
        print(E)
        abort(Err_NotProcessed)


# delete a drink
@app.route("/coffe/drinks/<int:drinkid>", methods=['DELETE'])
@requires_auth('delete:drinks')
def DeleteDrink(jwt_payload, drinkid):
    # lets get Drink id
    GetDrinkdata = Drink.query.filter(Drink.id == drinkid).one_or_none()
    # if there is no Drink Found then abort with 404
    if GetDrinkdata is None:
        abort(Err_Notfound)
    # otherwise lets try to delete the drink
    try:
        GetDrinkdata.delete()
        return jsonify({
            "delete": drinkid,
            "success": True
        })
    except Exception as E:
        print(E)
        abort(Err_NotProcessed)

# Error Handling
# 422 handler


@app.errorhandler(Err_NotProcessed)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": Err_NotProcessed,
        "message": "unprocessable"
    }), Err_NotProcessed
# 404 handler


@app.errorhandler(Err_Notfound)
def ErrNotfound(error):
    return jsonify({
        "success": False,
        "error": Err_Notfound,
        "message": "Not Found"
    }), Err_Notfound

# 401 handler


@app.errorhandler(Err_Unauth)
def ErrunAuth(error):
    return jsonify({
        "success": False,
        "error": Err_Unauth,
        "message": "unAuthorized attempt"
    }), Err_Unauth

# 400 handler


@app.errorhandler(Err_badrequest)
def ErrBadrequest(error):
    return jsonify({
        "success": False,
        "error": Err_badrequest,
        "message": "bad request"
    }), Err_badrequest

# 405 handler


@app.errorhandler(Err_NotAllowed)
def ErrNotAllowed(error):
    return jsonify({
        "success": False,
        "error": Err_NotAllowed,
        "message": "not allowed"
    }), Err_NotAllowed

# 500 handler


@app.errorhandler(Err_server)
def ErrServer(error):
    return jsonify({
        "success": False,
        "error": Err_server,
        "message": "Server Error"
    }), Err_server

# 503 handler


@app.errorhandler(Err_unavailable)
def ErrServerUnAvailabe(error):
    return jsonify({
        "success": False,
        "error": Err_unavailable,
        "message": "Server unavailable"
    }), Err_unavailable


if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=False)
