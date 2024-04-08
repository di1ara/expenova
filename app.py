from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import io
import base64


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

db = SQLAlchemy(app)

# Define Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Add user_id column
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)

# Create the database tables within an application context
with app.app_context():
    db.create_all()

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Username already exists')
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')
# Define the route for the landing page
@app.route('/landing')
def landing():
    return render_template('landing.html')

# Route for home page
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('landing'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    if user is None:
        return redirect(url_for('login'))

    expenses = user.expenses
    total_expense = sum(expense.amount for expense in expenses)
    category_totals = {}
    for expense in expenses:
        category = expense.category
        amount = expense.amount
        category_totals[category] = category_totals.get(category, 0) + amount
    
    # Generate chart data
    pie_chart_data = generate_pie_chart(category_totals)
    bar_chart_data = generate_bar_chart(category_totals)

    return render_template('index.html', expenses=expenses, total_expense=total_expense, category_totals=category_totals,
                           pie_chart_data=pie_chart_data, bar_chart_data=bar_chart_data)

# Function to generate pie chart
def generate_pie_chart(category_totals):
    labels = list(category_totals.keys())
    values = list(category_totals.values())

    plt.figure(figsize=(8, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Expense Distribution by Category')

    # Convert the plot to a base64 encoded string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    chart_data = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return chart_data

# Function to generate bar chart
def generate_bar_chart(category_totals):
    labels = list(category_totals.keys())
    values = list(category_totals.values())

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color='skyblue')
    plt.xlabel('Category')
    plt.ylabel('Total Amount')
    plt.title('Total Expense Amount by Category')

    # Convert the plot to a base64 encoded string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    chart_data = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return chart_data

# Route to handle adding new expenses
@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    category = request.form['category']
    amount = float(request.form['amount'])
    
    new_expense = Expense(user_id=user_id, category=category, amount=amount)
    db.session.add(new_expense)
    db.session.commit()
    
    return redirect(url_for('home'))



# Route to handle user logout
@app.route('/logout', methods=['POST'])
def logout():
    # Perform logout operations (e.g., clearing session data)
    session.clear()  # Assuming you are using Flask session

    # Redirect the user to the login page
    return redirect(url_for('login'))


# Run the Flask application if this script is executed directly
if __name__ == '__main__':
    app.run(debug=True)
