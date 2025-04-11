
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
import secrets
import uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")  # Replace with your Gmail
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Replace with your app password


# Database initialization
def init_db():
    # # Drop existing database if it exists to reset schema
    # if os.path.exists('rides.db'):
    #     os.remove('rides.db')

    conn = sqlite3.connect('rides.db')
    c = conn.cursor()

    # Create users table without password_hash
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create rides table
    c.execute('''
    CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        date TEXT NOT NULL,
        train_flight_time TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        start_location TEXT NOT NULL,
        destination TEXT NOT NULL,
        people_required INTEGER NOT NULL,
        cost_per_person INTEGER NOT NULL,
        vehicle_type TEXT NOT NULL,
        whatsapp_group_link TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create applications table
    c.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ride_id INTEGER NOT NULL,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (ride_id) REFERENCES rides (id),
        UNIQUE(user_id, ride_id)
    )
    ''')

    # Create suggestions table
    c.execute('''
    CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        suggestion TEXT NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()


# Initialize the database
init_db()

# Helper function to send emails
def send_email(recipient_email, subject, message_html):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_USERNAME
        msg['To'] = recipient_email
        msg['Subject'] = subject

        html_part = MIMEText(message_html, 'html')
        msg.attach(html_part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


# # Helper function to validate email
# def is_valid_vit_email(email):
#     # Check if email ends with @vitbhopal.ac.in
#     if not email.endswith('@vitbhopal.ac.in'):
#         return False
#
#     # Check if email follows the specific VIT pattern:
#     # string.YYcccNNNN@vitbhopal.ac.in
#     # where YY=2 numbers, ccc=3 letters, NNNN=4-5 numbers
#     pattern = r'^[a-zA-Z]+\.\d{2}[a-zA-Z]{3}\d{4,5}@vitbhopal\.ac\.in$'
#     return bool(re.match(pattern, email))

# Authentication Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')

        # Validate VIT Bhopal email domain
        # if not is_valid_vit_email(email):
        #     flash('Please a Valid VIT Bhopal email ', 'error')
        #     return render_template('login.html')

        conn = sqlite3.connect('rides.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()

        if not user:
            # User doesn't exist, create a new account
            c.execute("INSERT INTO users (email) VALUES (?)", (email,))
            conn.commit()
            user_id = c.lastrowid

            # Log the new user in
            session['user_id'] = user_id
            session['user_email'] = email

            conn.close()
            flash('Welcome to CabPoolVIT! Your account has been created.', 'success')
        else:
            # Log the existing user in
            session['user_id'] = user[0]
            session['user_email'] = user[1]

            conn.close()
            flash('Welcome back!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')

        # Validate VIT Bhopal email domain
        # if not is_valid_vit_email(email):
        #     flash('Please use your VIT Bhopal email', 'error')
        #     return render_template('signup.html')

        # Check if email already exists
        conn = sqlite3.connect('rides.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = c.fetchone()

        if existing_user:
            conn.close()
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('login'))

        # Create new user
        c.execute("INSERT INTO users (email) VALUES (?)", (email,))
        user_id = c.lastrowid
        conn.commit()
        conn.close()

        # Log the user in
        session['user_id'] = user_id
        session['user_email'] = email

        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_email = session['user_email']

    # Get user's rides
    conn = sqlite3.connect('rides.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT r.*, COUNT(a.id) as applications_count 
        FROM rides r 
        LEFT JOIN applications a ON r.id = a.ride_id 
        WHERE r.user_id = ? 
        GROUP BY r.id 
        ORDER BY r.date DESC
    """, (user_id,))
    user_rides = c.fetchall()

    # Get rides user has applied to
    c.execute("""
        SELECT r.*, u.email as owner_email
        FROM rides r
        JOIN applications a ON r.id = a.ride_id
        JOIN users u ON r.user_id = u.id
        WHERE a.user_id = ?
        ORDER BY r.date DESC
    """, (user_id,))
    applied_rides = c.fetchall()

    conn.close()

    return render_template('dashboard.html', user_rides=user_rides, applied_rides=applied_rides, user_email=user_email)


# Ride Routes
@app.route('/post-ride', methods=['GET', 'POST'])
def post_ride():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        ride_date = request.form.get('date')
        train_flight_time = request.form.get('train_flight_time')
        departure_time = request.form.get('departure_time')
        start_location = request.form.get('start_location')
        destination = request.form.get('destination')
        people_required = request.form.get('people_required')
        cost_per_person = request.form.get('cost_per_person')
        vehicle_type = request.form.get('vehicle_type')
        whatsapp_group_link = request.form.get('whatsapp_group_link')

        conn = sqlite3.connect('rides.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO rides (
                user_id, name, mobile, date, train_flight_time, 
                departure_time, start_location, destination, 
                people_required, cost_per_person, vehicle_type, whatsapp_group_link
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, name, mobile, ride_date, train_flight_time,
            departure_time, start_location, destination,
            people_required, cost_per_person, vehicle_type, whatsapp_group_link
        ))

        ride_id = c.lastrowid
        conn.commit()
        conn.close()

        # Fetch the ride for confirmation
        conn = sqlite3.connect('rides.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM rides WHERE id = ?", (ride_id,))
        ride = dict(c.fetchone())
        conn.close()

        flash("Ride posted successfully!", "success")
        return render_template('post_ride.html', confirmation=True, ride=ride)

    return render_template('post_ride.html')

@app.route('/find-ride', methods=['GET', 'POST'])
def find_ride():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    locations = [
        "Sant Hirdaram Station",
        "Bhopal Station",
        "Rani Kamlapati",
        "Bhopal Airport",
        "Indore Airport",
        "VIT College"
    ]

    conn = sqlite3.connect('rides.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        start_location = request.form.get('start_location')
        destination = request.form.get('destination')
        ride_date = request.form.get('date')

        query = """
            SELECT r.*, u.email as owner_email, COUNT(a.id) as applications_count
            FROM rides r
            JOIN users u ON r.user_id = u.id
            LEFT JOIN applications a ON r.id = a.ride_id
            WHERE 1=1
        """
        params = []

        if start_location and start_location != "Any":
            query += " AND r.start_location = ?"
            params.append(start_location)

        if destination and destination != "Any":
            query += " AND r.destination = ?"
            params.append(destination)

        if ride_date:
            query += " AND r.date = ?"
            params.append(ride_date)

        query += " GROUP BY r.id ORDER BY r.date ASC"

        c.execute(query, params)
        rides = c.fetchall()
    else:
        # Get upcoming rides
        today = date.today().strftime("%Y-%m-%d")
        c.execute("""
            SELECT r.*, u.email as owner_email, COUNT(a.id) as applications_count
            FROM rides r
            JOIN users u ON r.user_id = u.id
            LEFT JOIN applications a ON r.id = a.ride_id
            WHERE r.date >= ?
            GROUP BY r.id
            ORDER BY r.date ASC
        """, (today,))
        rides = c.fetchall()

    # Check which rides the user has already applied to
    c.execute("SELECT ride_id FROM applications WHERE user_id = ?", (user_id,))
    applied_ride_ids = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template('find_ride.html',
                           rides=rides,
                           locations=locations,
                           applied_ride_ids=applied_ride_ids,
                           user_id=user_id)


@app.route('/edit-ride/<int:ride_id>', methods=['GET', 'POST'])
def edit_ride(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = sqlite3.connect('rides.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get ride details
    c.execute("SELECT * FROM rides WHERE id = ? AND user_id = ?", (ride_id, user_id))
    ride = c.fetchone()

    if not ride:
        conn.close()
        flash("Ride not found or you don't have permission to edit it", "error")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        ride_date = request.form.get('date')
        train_flight_time = request.form.get('train_flight_time')
        departure_time = request.form.get('departure_time')
        start_location = request.form.get('start_location')
        destination = request.form.get('destination')
        people_required = request.form.get('people_required')
        cost_per_person = request.form.get('cost_per_person')
        vehicle_type = request.form.get('vehicle_type')
        whatsapp_group_link = request.form.get('whatsapp_group_link')

        c.execute("""
            UPDATE rides 
            SET name = ?, mobile = ?, date = ?, train_flight_time = ?, departure_time = ?,
                start_location = ?, destination = ?, people_required = ?, cost_per_person = ?,
                vehicle_type = ?, whatsapp_group_link = ?
            WHERE id = ? AND user_id = ?
        """, (
            name, mobile, ride_date, train_flight_time, departure_time,
            start_location, destination, people_required, cost_per_person,
            vehicle_type, whatsapp_group_link, ride_id, user_id
        ))
        conn.commit()

        # Get updated ride for confirmation
        c.execute("SELECT * FROM rides WHERE id = ?", (ride_id,))
        updated_ride = dict(c.fetchone())
        conn.close()

        flash("Ride updated successfully!", "success")
        return render_template('edit_ride.html', ride=ride, confirmation=True, updated_ride=updated_ride)

    conn.close()
    return render_template('edit_ride.html', ride=ride)


@app.route('/delete-ride/<int:ride_id>')
def delete_ride(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = sqlite3.connect('rides.db')
    c = conn.cursor()

    # First delete applications
    c.execute("DELETE FROM applications WHERE ride_id = ?", (ride_id,))

    # Then delete the ride
    c.execute("DELETE FROM rides WHERE id = ? AND user_id = ?", (ride_id, user_id))

    conn.commit()
    conn.close()

    flash("Ride deleted successfully", "success")
    return redirect(url_for('dashboard'))


@app.route('/apply-ride/<int:ride_id>')
def apply_ride(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_email = session['user_email']

    conn = sqlite3.connect('rides.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Check if already applied
    c.execute("SELECT * FROM applications WHERE user_id = ? AND ride_id = ?", (user_id, ride_id))
    existing_application = c.fetchone()

    if existing_application:
        conn.close()
        flash("You have already applied to this ride", "info")
        return redirect(url_for('find_ride'))

    # Get ride details
    c.execute("""
        SELECT r.*, u.email as owner_email, COUNT(a.id) as applications_count
        FROM rides r 
        JOIN users u ON r.user_id = u.id 
        LEFT JOIN applications a ON r.id = a.ride_id
        WHERE r.id = ?
        GROUP BY r.id
    """, (ride_id,))

    ride = c.fetchone()

    if not ride:
        conn.close()
        flash("Ride not found", "error")
        return redirect(url_for('find_ride'))

    # Check if the ride is already full
    if ride['applications_count'] >= ride['people_required']:
        conn.close()
        flash("This ride is already full", "error")
        return redirect(url_for('find_ride'))

    # Insert application
    c.execute("INSERT INTO applications (user_id, ride_id) VALUES (?, ?)", (user_id, ride_id))
    conn.commit()
    conn.close()

    # Send email to the applicant with the WhatsApp group link
    subject = f"CabPoolVIT: You applied for a ride on {ride['date']}"
    message_html = f"""
    <html>
      <head>
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
          .container {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
          .header {{ background-color: #068a32; color: white; padding: 10px 20px; border-radius: 8px 8px 0 0; }}
          .content {{ background-color: #f7f7f7; padding: 20px; border-radius: 0 0 8px 8px; }}
          .button {{ display: inline-block; background-color: #59e309; color: white; padding: 10px 15px; text-decoration: none; border-radius: 8px; margin-top: 15px; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>CabPoolVIT: Ride Application</h1>
          </div>
          <div class="content">
            <h2>You've successfully applied for a ride!</h2>
            <p>Here are the details of the ride:</p>
            <ul>
              <li><strong>From:</strong> {ride['start_location']}</li>
              <li><strong>To:</strong> {ride['destination']}</li>
              <li><strong>Date:</strong> {ride['date']}</li>
              <li><strong>Train/Flight Time:</strong> {ride['train_flight_time']}</li>
              <li><strong>Departure Time:</strong> {ride['departure_time']}</li>
              <li><strong>Vehicle Type:</strong> {ride['vehicle_type']}</li>
              <li><strong>Cost Per Person:</strong> ₹{ride['cost_per_person']}</li>
            </ul>
            <p>Join the WhatsApp group to coordinate with your fellow travelers:</p>
            <a href="{ride['whatsapp_group_link']}" class="button">Join WhatsApp Group</a>
            <p>If you have any questions, you can contact the ride owner through the WhatsApp group.</p>
            <p>Thank you for using CabPoolVIT!</p>
          </div>
        </div>
      </body>
    </html>
    """

    try:
        send_email(user_email, subject, message_html)
        # Also notify the ride owner
        owner_subject = f"CabPoolVIT: New application for your ride on {ride['date']}"
        owner_message = f"""
        <html>
          <head>
            <style>
              body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
              .container {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
              .header {{ background-color: #068a32; color: white; padding: 10px 20px; border-radius: 8px 8px 0 0; }}
              .content {{ background-color: #f7f7f7; padding: 20px; border-radius: 0 0 8px 8px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h1>CabPoolVIT: New Ride Application</h1>
              </div>
              <div class="content">
                <h2>Someone applied for your ride!</h2>
                <p>{user_email} has applied to join your ride from {ride['start_location']} to {ride['destination']} on {ride['date']}.</p>
                <p>They have been sent the WhatsApp group link.</p>
                <p>Check your dashboard to see all applications.</p>
              </div>
            </div>
          </body>
        </html>
        """
        send_email(ride['owner_email'], owner_subject, owner_message)
    except Exception as e:
        print(f"Email error: {str(e)}")

    # Show a confirmation dialog
    flash("Application successful! WhatsApp group link has been sent to your email."
          "If not then please check the spam mail section.", "success")
    return redirect(url_for('find_ride'))


@app.route('/leave-ride/<int:ride_id>')
def leave_ride(ride_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = sqlite3.connect('rides.db')
    c = conn.cursor()

    # Check if the application exists
    c.execute("SELECT * FROM applications WHERE user_id = ? AND ride_id = ?", (user_id, ride_id))
    application = c.fetchone()

    if not application:
        conn.close()
        flash("You haven't applied to this ride.", "error")
        return redirect(url_for('dashboard'))

    # Delete the application
    c.execute("DELETE FROM applications WHERE user_id = ? AND ride_id = ?", (user_id, ride_id))
    conn.commit()
    conn.close()

    flash("You have left the ride successfully.", "success")
    return redirect(url_for('dashboard'))


@app.route('/suggestions', methods=['GET', 'POST'])
def suggestions():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        suggestion = request.form.get('suggestion')

        conn = sqlite3.connect('rides.db')
        c = conn.cursor()
        c.execute("INSERT INTO suggestions (user_id, suggestion) VALUES (?, ?)",
                  (user_id, suggestion))
        conn.commit()
        conn.close()

        flash("Thank you for your suggestion!", "success")
        return redirect(url_for('suggestions'))

    # Get spreadsheet link
    conn = sqlite3.connect('rides.db')
    c = conn.cursor()
    # For simplicity, the spreadsheet link is hardcoded here
    spreadsheet_link = "https://docs.google.com/spreadsheets/d/11_lCM299f1gByvz4hLOHR3yuEbP77NsZBSCtOf7l0aw/edit?usp=sharing"
    conn.close()

    return render_template('suggestions.html', spreadsheet_link=spreadsheet_link)


@app.route('/about')
def about():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Developer information can be edited further
    developers = [
        {
            'name': 'Abhinav Kumar',
            'reg': '24BSA',
            'email': 'abhinavkumarsaksena@gmail.com',
            'linkedin': 'https://www.linkedin.com/in/abhinav-kumar-9193632b3/'
        },
        {
            'name': 'Aditya Verma',
            'reg': '24BCE',
            'email': 'aditya2809verma@gmail.com',
            'linkedin': 'https://www.linkedin.com/in/aditya-verma-0a2465324/'
        }
    ]

    return render_template('about.html', developers=developers)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
