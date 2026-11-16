Employee Leave Portal

A simple leave management website. Employees apply for leave, and admins approve or reject it.

Built with: HTML, CSS, JavaScript, Python (Django), MySQL

Features

Employee

Log in and see leave balance
Apply for leave
Check request status (Pending, Approved, Rejected)
View leave history

Admin

Log in as admin
See all leave requests and filter them
Approve or reject (with a reason)
View employee balances and reports
Download reports as CSV

Requirements
Python 3.12 or 3.13
MySQL 8
Git

For Windows

Open Command Prompt and follow these steps one by one.

Step 1: Download the project

git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

Step 2: Create the database

mysql -u root -p < database\setup.sql

Enter your MySQL root password when asked.

Step 3: Create a virtual environment

python -m venv venv
venv\Scripts\activate

Step 4: Install packages

pip install -r requirements.txt

Step 5: Create tables and sample data

python manage.py migrate
python manage.py seed_data

Step 6: Start the app

python manage.py runserver

Step 7: Open in browser

Go to http://127.0.0.1:8000


Usage

Log in with these demo accounts:

Role	Email	Password

For Example Admin   	admin@company.com	Password Admin@123
For Example Employee	arun@company.com	Password Employee@123

We need to create the admin and employee user id and password 

leave_portal/
├── manage.py            # runs the project
├── requirements.txt     # packages needed
├── database/            # database setup script
├── leave_portal/        # project settings
├── leaves/              # main app code
├── templates/           # HTML pages
└── static/              # CSS and JavaScript

Future Improvements

>Email notification when a request is approved or rejected
>Employees can cancel a pending request
>Half-day and hourly leave permission
>Manager level approval before admin
>Password reset using email






