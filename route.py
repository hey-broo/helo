from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root@123',
    'database': 'your_database'
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['userid']
        password = request.form['password']

        try:
            # Generate OTP and store it in session
            otp = random.randint(100000, 999999)
            session['otp'] = otp
            session['user_data'] = {'email': email, 'username': username, 'password': password}

            # Send OTP to user (for now, just display it in the alert)
            return jsonify({'otp': otp})

        except Exception as e:
            return jsonify({'error': str(e)})

    return render_template('index.html')

@app.route('/otp', methods=['POST'])
def otp():
    entered_otp = request.form['otp']
    stored_otp = session.get('otp')

    if str(stored_otp) == entered_otp:
        try:
            user_data = session.get('user_data')
            email = user_data['email']
            username = user_data['username']
            password = user_data['password']

            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO helo (email, username, password) VALUES (%s, %s, %s)", (email, username, password))
            connection.commit()
            cursor.close()
            connection.close()

            return jsonify({'success': True, 'message': 'OTP Verified! Redirecting...'})

        except Exception as e:
            return jsonify({'success': False, 'message': "Error saving data: " + str(e)})

    return jsonify({'success': False, 'message': "Invalid OTP. Please try again."})

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('userid')
        password = request.form.get('password')

        # Connect to database and check if user exists
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM helo WHERE (username = %s OR email = %s) AND password = %s", 
                       (username, username, password))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({"error": "User does not exist!"})  # If user not found, return message

        # Generate OTP and store in session
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['username'] = username
        conn.close()

        return jsonify({"otp": otp})  # Send OTP to frontend

    return render_template('login.html')

# Renamed this route to avoid conflict with the first OTP route
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otp')

    if 'otp' in session and session['otp'] == entered_otp:
        session.pop('otp', None)  # Remove OTP after verification
        return jsonify({"success": True, "message": "OTP Verified! Redirecting..."}), 200
    else:
        return jsonify({"success": False, "message": "Invalid OTP. Try again!"}), 400

if __name__ == '__main__':
    app.run(debug=True)
