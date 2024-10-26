---

# **Purchase Manager**

### **A Cross-Platform App for Managing Bills and Warranty Invoices**

**Purchase Manager** is a mobile and web application designed to help users securely store and organize bills and warranty invoices for their purchased products. The app is built with **React Native** for the frontend, ensuring compatibility with Android, iOS, and web, and uses **Python Flask** as the backend with **MongoDB** as the database. This entire application is containerized with **Docker** to simplify deployment and scalability.

---

## **Table of Contents**

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Setup and Installation](#setup-and-installation)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## **Features**

- **User Authentication**: Secure login, registration, and profile management.
- **Invoice Storage**: Add, view, and search through uploaded invoices.
- **Warranty Alerts**: Set alerts for warranty expiration notifications.
- **Data Export**: Export selected invoices as PDF files.
- **Cross-Platform Support**: Runs on Android, iOS, and Web.
- **Containerized Deployment**: Easily deployable with Docker.

---

## **Technology Stack**

- **Frontend**: React Native with Expo for cross-platform compatibility
- **Backend**: Python Flask REST API
- **Database**: MongoDB (MongoDB Atlas for cloud database)
- **Containerization**: Docker
- **Notifications**: Push notifications for mobile, email reminders for web

---

## **Setup and Installation**

### **Requirements**

- **Node.js** (for React Native)
- **Python 3.9+** (for Flask API)
- **Docker** (for containerized deployment)
- **MongoDB** (local or MongoDB Atlas)

### **Installation Steps**

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/purchase-manager.git
   cd purchase-manager
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install  # or yarn install
   ```

3. **Backend Setup**
   ```bash
   cd ../backend
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **MongoDB Setup**
   - If using MongoDB locally, ensure it’s running on port 27017.
   - If using MongoDB Atlas, get your connection URI and add it to `MONGO_URI` in `.env`.

5. **Environment Variables**
   - Create a `.env` file in the `backend` folder with the following variables:
     ```
     MONGO_URI=<your_mongodb_uri>
     SECRET_KEY=<your_secret_key>
     ```

6. **Run with Docker (Recommended)**
   - Ensure Docker is installed and running, then use `docker-compose` to spin up the services:
     ```bash
     docker-compose up --build
     ```

   - The frontend will be accessible at `http://localhost:3000` and the backend at `http://localhost:5000`.

---

## **Project Structure**

### **Frontend (React Native)**

```
frontend/
│── components/      # Reusable UI components
│── screens/         # Screens for navigation
│── services/        # API calls and services
│── App.js           # Main app entry
```

### **Backend (Flask)**

```
backend/
│── app/
│   ├── models.py            # Database models
│   ├── routes/              # API routes
│   ├── utils/               # Utility functions
│── config.py                # Configuration setup
│── requirements.txt         # Dependencies
│── Dockerfile               # Dockerfile for backend
```

---

## **API Documentation**

### **Authentication**
   - **POST /register** - Register a new user
   - **POST /login** - Authenticate a user
   - **GET /profile** - Retrieve user profile

### **Invoice Management**
   - **POST /invoice/add** - Add a new invoice
   - **GET /invoice/list** - Retrieve user invoices
   - **GET /invoice/search** - Search for invoices
   - **DELETE /invoice/delete** - Delete an invoice

### **Notifications**
   - **POST /notifications/add** - Set a warranty expiration alert
   - **GET /notifications/list** - Retrieve notifications

### **Data Export**
   - **POST /export** - Export selected invoices

---

## **Deployment**

### **Docker Deployment**

1. **Build and Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Frontend (Expo)**:
   - For web deployment, use `yarn build` in the `frontend` folder.
   - For mobile apps, generate APK/IPA files using Expo and distribute via app stores.

3. **Backend**:
   - Deploy the Dockerized backend on cloud services like AWS ECS, DigitalOcean, or Heroku.

---

## **Contributing**

Contributions are welcome! Please fork the repository and create a pull request to add any features, fix bugs, or improve documentation.

---
