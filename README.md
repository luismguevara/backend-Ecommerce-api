# E-Commerce Backend API

RESTful backend API developed with **Python Flask** to support an Android
e-commerce application.  
The API manages user authentication, product catalog data, orders, and messaging
features used by the mobile client.

## Features

- User registration and authentication
- Product catalog management
- Order creation and management
- Customer purchase history
- Admin product management
- Chat messaging support between client and store

## Technologies

- Python
- Flask
- REST API architecture
- JSON data exchange
- Relational SQL database (MySQL)

## API Responsibilities

The backend is responsible for:

- Handling client authentication
- Managing product inventory
- Processing customer orders
- Storing user purchase history
- Managing administrative product actions

## Project Structure

- App.py
- models.py
- requeriments.txt
- endpoints/
- database/

## Usage

Run the Flask Server: python App.py

The API will start locally and can be accessed by the Android client.

## Purpose

This project was developed to support a full-stack mobile commerce system,
integrating this backend API with an Android application.

## Instalation

- Clone the repository:

git clone https://github.com/luismguevara/backend-Ecommerce-api.git

- Create a virtual environment:

python -m venv virt

- Activate the environment:

Windows: .\virt\Scripts\activate

- Install dependencies:

pip install -r requirements.txt

- Run the server:

python app.py

**THIS API IS USED BY THE ANDROID CLIENT:**
https://github.com/luismguevara/android-Ecommerce-app

## Author

Luis Guevara - Backend Developer
