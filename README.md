# Temple POS System

A Point of Sale (POS) system designed for Hindu temples, with support for multiple services and user roles.

## Features
- User authentication with role-based access (Admin and Clerk)
- Modern and responsive UI using Bootstrap
- Secure password hashing
- SQLite database (easily upgradeable to other databases)

## Setup Instructions

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the application:
Open a web browser and navigate to `http://localhost:5000`

## Deployment on Raspberry Pi
1. Clone this repository
2. Install dependencies
3. Configure the system to run the application on startup
4. Access the application through the Raspberry Pi's IP address

## Security Note
Please change the default admin password after first login.
