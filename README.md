# K Wallet - Digital Payment System

A Flask-based digital wallet application for secure money transfers with QR code payments.

## Features

- User registration and authentication
- Money transfers between accounts
- QR code payment generation
- Transaction history
- Profile management with photo upload
- Admin dashboard for system statistics

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: SQLite (development), PostgreSQL (production)
- **Security**: Werkzeug (password hashing)
- **File Handling**: Pillow, qrcode

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/shemoigara8-sys/bank-wallet.git
cd bank-wallet
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create directories
```bash
mkdir -p static/uploads static/qrcodes
```

### 5. Run the application
```bash
python app.py
```

Access the app at `http://localhost:5000`

## Environment Variables

Create a `.env` file in the root directory:

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///kwallet.db
FLASK_ENV=development
```

## Project Structure

```
bank-wallet/
├── app.py                 # Application factory
├── models.py              # Database models
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
├── routes/                # API blueprints
│   ├── auth.py           # Authentication routes
│   ├── wallet.py         # Wallet operations
│   └── admin.py          # Admin dashboard
├── templates/            # HTML templates
├── static/               # CSS, JS, images
└── README.md
```

## API Endpoints

### Authentication
- `POST /register` - Create new account
- `POST /login` - User login
- `GET /logout` - User logout

### Wallet
- `GET /balance` - Get account balance
- `POST /send` - Send money
- `GET /history` - Transaction history
- `POST /upload_photo` - Upload profile photo
- `GET /qr` - Generate QR code

### Admin
- `GET /admin` - Admin dashboard
- `GET /admin/stats` - System statistics
- `GET /admin/users` - List all users
- `GET /admin/transactions` - Recent transactions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.
