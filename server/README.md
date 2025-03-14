# Preventative Maintenance Update

This project is a simple maintenance tracker application with a client and server. The client is built with React, and the server is built with Flask and SQLite.

## Prerequisites

- Node.js
- npm (Node Package Manager)
- Python
- pip (Python Package Installer)

## Getting Started

### Clone the Repository

```sh
git clone https://github.com/yourusername/Copilot-Preventative-Maintenance-Update.git
cd Copilot-Preventative-Maintenance-Update
```

### Install Dependencies

#### Client

```sh
cd client
npm install
```

#### Server

```sh
cd ../server
pip install flask flask_sqlalchemy flask_cors
```

## Running the Application

### Start the Server

```sh
cd server
python app.py
```

The server will start on `http://0.0.0.0:5001`.

### Start the Client

Open a new terminal window and run:

```sh
cd client
npm start
```

The client will start on `http://localhost:3000`.

### Accessing the Application

Open your web browser and navigate to `http://localhost:3000` to view and test the client interface.

### Login

Use the following credentials to log in:

- **Username:** admin
- **Password:** password

## API Endpoints

### Create a new maintenance record

- **URL:** `/maintenance`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "machine": "Machine Name",
    "part": "Part Name",
    "description": "Description of the maintenance",
    "date": "YYYY-MM-DD"
  }
  ```

### Read all maintenance records

- **URL:** `/maintenance`
- **Method:** `GET`

### Update a maintenance record

- **URL:** `/maintenance/:id`
- **Method:** `PUT`
- **Body:**
  ```json
  {
    "machine": "Updated Machine Name",
    "part": "Updated Part Name",
    "description": "Updated description of the maintenance",
    "date": "YYYY-MM-DD"
  }
  ```

### Delete a maintenance record

- **URL:** `/maintenance/:id`
- **Method:** `DELETE`

## License

This project is licensed under the MIT License.
