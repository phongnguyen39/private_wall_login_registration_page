# Private_wall assignment

from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = 'secret'
bcrypt = Bcrypt(app)

# DETECT IP address
# from flask import request
# from flask import jsonify

# @app.route("/get_my_ip", methods=["GET"])
# def get_my_ip():
#     return jsonify({'ip': request.remote_addr}), 200

# Create a way to message into table It needs to direct to back to sender
# CREATE IP LOGGED IN TABLE

# Link to danger warning page
# add delete button (SQL HTML)


EMAIL_REGEX = re.compile(r'^[a-zA-z0-9.+_-]+@[a-zA-z0-9.+_-]+\.[a-zA-Z]+$')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registration', methods=['post'])
def registration():

    session['first_name'] = request.form['first_name']
    session['last_name'] = request.form['last_name'],
    session['emails'] = request.form['emails']

    is_valid = True

    if len(request.form['first_name']) < 3:
        is_valid = False
        # print('*'*10, False, '*'*10)
        flash('Please enter a first name that is at least two characters long')
        return redirect('/')

    if len(request.form['last_name']) < 3:
        is_valid = False
        # print('*'*10, False, '*'*10)
        flash('Please enter a last name that is at least two characters long')
        return redirect('/')

    if not EMAIL_REGEX.match(request.form['emails']):
        flash(f'"{request.form["emails"]}"" is invalid')
        return redirect('/')

    login_reg = connectToMySQL('login_reg_messages')
    query = 'SELECT * FROM login_reg WHERE emails = %(emails)s'
    data = {
        'emails': request.form['emails']
    }
    existing_email = login_reg.query_db(query, data)
    if len(existing_email) > 0:
        flash('Email already exist.')
        print(('~'*20))
        return redirect('/')

    # SELECT email FROM login_reg WHERE = request.form['email']
    # if request.form['email'] 

    if len(request.form['password']) < 8:
        is_valid = False
        # print('*'*10, False, '*'*10)
        flash('Please enter a password name that is at least 8 characters long')
        return redirect('/')

    if request.form['password'] != request.form['password_conf']:
        is_valid = True
        flash('Make sure your passwords match')
        return redirect('/')

    if is_valid:
        login_reg = connectToMySQL('login_reg_messages')
        query = 'INSERT INTO login_reg (first_names, last_names, emails, passwords_hash) VALUES (%(first_name)s,%(last_name)s,%(email)s,%(password)s);'
        data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['emails'],
            'password': bcrypt.generate_password_hash(request.form['password'])
        }

        login_reg = login_reg.query_db(query, data)
        flash("You've successfully registered!")
        return redirect('/wall')


@app.route('/login', methods=['post'])
def login():

    session['emails'] = request.form['emails']

    is_valid = True

    if not EMAIL_REGEX.match(request.form['emails']):
        flash(f'"{request.form["emails"]}"" is invalid')
        return redirect('/')

    login_reg = connectToMySQL('login_reg_messages')
    query = 'SELECT * FROM login_reg WHERE emails = %(emails)s'
    data = {
        'emails': request.form['emails']
    }

    logins = login_reg.query_db(query, data)
    
    session['id'] = logins[0]['id']
    session['emails'] = logins[0]['emails']

    if len(logins) == 0:
        flash("Failed login! Email not found.")
        return redirect('/')

    if logins:
        if bcrypt.check_password_hash(logins[0]['passwords_hash'], request.form['password']):
            flash("Logged in successfully!")
            return redirect('/wall')
        else:
            flash("Failed login! Password was incorrect.")
            return redirect('/')

@app.route('/wall')
def wall():


    #Used to view messages on page
    login_reg = connectToMySQL('login_reg_messages')
    query = 'select * from login_reg JOIN messages ON login_reg.id = messages.receiver_id WHERE login_reg.emails = %(emails)s;'
    data = {
        'emails' : session['emails']
    }

    #Incoming messages log
    messages = login_reg.query_db(query,data)
    count_messages = len(messages)

    #User's First Name
    login_reg = connectToMySQL('login_reg_messages')
    query = 'select first_names from login_reg WHERE login_reg.emails = %(emails)s;'
    data = {
        'emails' : session['emails']
    }
    user_name = login_reg.query_db(query,data)

    #Gets name of the sender
    login_reg = connectToMySQL('login_reg_messages')
    query = 'select * from login_reg JOIN messages ON login_reg.id = messages.sender_id WHERE login_reg.emails = %(emails)s;'

    data = {
        'emails' : session['emails']
    }
    sender_name = login_reg.query_db(query,data)
    count_sent = len(sender_name)
    ####### Count messsages sent by user  

    #Used to populate dropdown list of receivers
    login_reg = connectToMySQL('login_reg_messages')
    query2 = 'SELECT * FROM login_reg'
    dropdown_names = login_reg.query_db(query2)
    
    return render_template('wall.html', messages = messages, count_messages = count_messages, count_sent = count_sent, dropdown_names = dropdown_names, sender_name = sender_name,user_name = user_name)  

#Stores messages sent
@app.route('/message', methods=['post'])
def message():
    login_reg = connectToMySQL('login_reg_messages')
    query = 'SELECT login_reg.id FROM login_reg WHERE login_reg.emails = %(emails)s;'
    data = {'emails': session['emails']}
    user_id = login_reg.query_db(query, data)

    login_reg = connectToMySQL('login_reg_messages')
    query = 'INSERT INTO messages (sender_id, receiver_id, messages) VALUES (%(sender_id)s,%(receiver_id)s, %(messages)s);'
    data = {
        'sender_id': user_id[0]['id'], 
        'receiver_id': request.form['receiver_id'],
        'messages': request.form['message']
    }
    messages = login_reg.query_db(query, data)
    flash('Message sent successfully!')
    return redirect('/wall')

@app.route('/danger')
def danger():
    return render_template('danger.html')

@app.route('/delete/<id>')
def delete(id):
    # print(request.form["message_id_delete"])
    print('*'*50)
    login_reg = connectToMySQL('login_reg_messages')
    query = 'DELETE FROM messages WHERE id = %(id)s'
    data = {
        'id': int(id)
    }
    login_reg = login_reg.query_db(query,data)
    return redirect('/wall')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
