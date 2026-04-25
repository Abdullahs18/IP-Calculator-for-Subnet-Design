Computer Networks Project
# IP Calculator & Subnet Design Tool

A comprehensive web-based networking utility built with Python (Flask) and a modern, responsive frontend. This tool provides powerful features for network engineers, students, and IT professionals to design, allocate, and analyze IPv4 subnets efficiently.

## ✨ Features

- **IPv4 Calculator**: Calculate network addresses, broadcast addresses, usable host ranges, subnet masks, wildcard masks, and binary representations from any given IP and CIDR prefix.
- **VLSM Allocator**: Implement Variable Length Subnet Masking (VLSM). Input a base network and a list of required host sizes, and the algorithm will automatically allocate the most efficient subnets (largest-first allocation) without overlapping. Includes CSV export functionality!
- **Subnet Compare**: Instantly check if two different IP addresses belong to the exact same subnet based on a given subnet mask.
- **Supernetting (Route Aggregation)**: Input multiple contiguous subnets to calculate their optimized, aggregated Supernet route.

## 🛠️ Technology Stack

- **Backend**: Python 3, Flask, `ipaddress` module
- **Frontend**: HTML5, Vanilla CSS (modern dark-mode UI), Vanilla JavaScript
- **Server**: Gunicorn (Ready for production deployment)

## 🚀 How to Run Locally

You don't need to deploy this project to the internet to use it! You can run it locally on your own machine.

### Prerequisites
Make sure you have [Python](https://www.python.org/downloads/) installed on your computer. 

### Installation
1. Clone this repository or download the project files.
2. Open your terminal and navigate to the project directory:
   ```bash
   cd "CN Project"
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
1. Start the Flask local development server:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   **`http://127.0.0.1:5000`**

To stop the server, press `Ctrl + C` in your terminal.

## 🌍 Network / LAN Access
The application is configured to listen on `0.0.0.0`. This means that while the server is running on your computer, you can access it from your phone or any other device on the same Wi-Fi network by navigating to your computer's local IP address (e.g., `http://192.168.1.X:5000`).

## 📦 Deployment Ready
This project includes a `Procfile` and uses `gunicorn` in its `requirements.txt`, making it 100% ready to be deployed to cloud platforms like Render, Heroku, or PythonAnywhere.
