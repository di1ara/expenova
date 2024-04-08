# Import necessary functions and classes from Flask
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
app.config['DATABASE'] = 'expenses.db'

# Function to establish a connection to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database with the schema
def initialize_database():
    with app.app_context():
        db = get_db_connection()
        db.execute('''CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        amount REAL NOT NULL
                     )''')
        db.commit()
        db.close()

# Initialize the database when the application starts
initialize_database()

# Route to handle adding new expenses
@app.route('/add_expense', methods=['POST'])
def add_expense():
    category = request.form['category']
    amount = float(request.form['amount'])
    
    db = get_db_connection()
    db.execute('INSERT INTO expenses (category, amount) VALUES (?, ?)', (category, amount))
    db.commit()
    db.close()
    
    return redirect(url_for('home'))

# Home route to display the expense report
@app.route('/')
def home():
    db = get_db_connection()
    expenses = db.execute('SELECT * FROM expenses').fetchall()
    
    # Calculate total expense
    total_expense = sum(expense['amount'] for expense in expenses)
    
    # Calculate category totals
    category_totals = {}
    for expense in expenses:
        category = expense['category']
        amount = expense['amount']
        category_totals[category] = category_totals.get(category, 0) + amount
    
    db.close()
    
    return render_template('index.html', expenses=expenses, total_expense=total_expense, category_totals=category_totals)


# Run the Flask application if this script is executed directly
if __name__ == '__main__':
    app.run(debug=True)
