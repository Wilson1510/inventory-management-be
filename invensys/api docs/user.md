# API Endpoints and Payload

## List
**Endpoint:** `GET /api/users/`

**Response:**
```json
[
    {
        "id": 1,
        "username": "admin",
        "email": "admin@mail.com",
        "name": "System Admin",
        "role": "admin",
        "is_active": true
    },
    {
        "id": 2,
        "username": "staff1",
        "email": "staff@mail.com",
        "name": "Warehouse Staff",
        "role": "staff",
        "is_active": true
    }
]
```

## Retrieve
**Endpoint:** `GET /api/users/{id}`
**Response:**
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@mail.com",
    "name": "System Admin",
    "role": "admin",
    "is_active": true
}
```

## Create
**Endpoint:** `POST /api/users/`
**Request Body:**
```json
{
    "username": "admin",
    "email": "admin@mail.com",
    "name": "System Admin",
    "role": "admin",
    "is_active": true
}
```
**Response:**
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@mail.com",
    "name": "System Admin",
    "role": "admin",
    "is_active": true
}
```

## Update (PUT and PATCH)
**Endpoint:** `PUT /api/users/{id}`
**Request Body:**
PUT send all fields
PATCH send only changed fields
```json
{
    "username": "admin",
    "email": "admin@mail.com",
    "name": "System Admin",
    "role": "admin",
    "is_active": true
}
```
**Response:**
PUT send all fields
PATCH send only changed fields
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@mail.com",
    "name": "System Admin",
    "role": "admin",
    "is_active": true
}
```

## Delete
**Endpoint:** `DELETE /api/users/{id}`
**Response:** `204 No Content`

## Reset Password
**Endpoint:** `PATCH /api/users/{id}/reset-password/`
**Request Body:**
```json
{
    "new_password": "password123",
    "confirm_password": "password123"
}
```
**Response:**
```json
{
    "message": "Password reset successfully"
}
```

## Get Profile Info
**Endpoint:** `GET /api/users/me/`

**Response:**
```json
{
    "id": 2,
    "username": "wilson",
    "email": "wilson.soeparman@gmail.com",
    "name": "Wilson Soeparman",
    "role": "staff",
    "is_active": true
}
```

## Update Profile Info
**Endpoint:** `PATCH /api/users/me/`
**Request Body:**
```json
{
    "username": "wilson",
    "email": "wilson.soeparman@gmail.com",
    "name": "Wilson Soeparman"
}
```
**Response:**
```json
{
    "id": 2,
    "username": "wilson",
    "email": "wilson.soeparman@gmail.com",
    "name": "Wilson Soeparman",
    "role": "staff",
    "is_active": true
}
```

## Change Password
**Endpoint:** `PATCH /api/users/me/change-password/`
**Request Body:**
```json
{
    "old_password": "password123",
    "new_password": "password456",
    "confirm_password": "password456"
}
```
**Response:**
```json
{
    "message": "Password changed successfully"
}
```