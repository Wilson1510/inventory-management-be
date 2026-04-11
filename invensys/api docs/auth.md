# API Endpoints and Payload

## Issue Token (Login)
**Endpoint:** `POST /api/auth/login/`
**Request Body:**
```json
{
    "username": "admin",
    "password": "password123"
}
```
**Response:**
```json
{
    "access": "jwt-access-token",
    "refresh": "jwt-refresh-token",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@mail.com",
        "name": "System Admin",
        "role": "admin"
    }
}
```