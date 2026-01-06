🐳 Docker SaaS Container Manager

Project Presentation : 

I built a SaaS platform for managing Docker containers. It allows users to create, start, stop, and delete their own Nginx containers through a web interface. Each user has an isolated environment where they can only see and manage their own containers
## 🎯 Features

- **User Authentication**: Secure login/registration 
- **Isolated Environments**: Each user manages only their own containers
- **Container Lifecycle Management**: Create, start, stop, and delete containers
- **Custom Nginx Containers**: Deploy containers with personalized HTML pages
- **Real-time Status**: Live container status monitoring
- **Docker API Integration**: Direct communication with Docker daemon

## 📋 Requirements

- **Operating System**: Linux  (Ubuntu)
- **Python**: 3.12.3
- **Docker**: 28.2.2 

## 🚀 Installation Steps

### 1. Install Docker 

#### On Ubuntu/Debian:
sudo apt-get update

sudo apt-get install -y docker.io

sudo systemctl start docker

sudo systemctl enable docker

#### Add your user to docker group:

sudo usermod -aG docker $USER

newgrp docker


### 2. Install Python Dependencies

# Create virtual environment

python3 -m venv venv

source venv/bin/activate  

# Install packages

pip install -r requirements.txt


## 🎮 Usage

### Starting the Application

# Activate virtual environment

source venv/bin/activate

# Run the application

python3 app.py


The application will be available at: **http://localhost:5000**

### Default User Accounts


| Username | Password | Email |
|----------|----------|-------|
| soltani | amal123 | amal@example.com |
| amadou | amadou123 | amadou@example.com |


### Managing Containers

- **Start**: Start a stopped container
- **Stop**: Stop a running container
- **Delete**: Remove container permanently

## 🏗️ Project Structure

docker-manager/

├── 📄 app.py   

├── ⚙️ config.py       

├── 💾 models.py   

├── 🐳 docker_manager.py 

├── 📋 requirements.txt  

├── 📖 README.md         

│
├── 📁 templates/                # Templates HTML
│   ├── base.html
│   ├── login.html
│   └── dashboard.html

│
├── 📁 static/                   # Fichiers statiques
│   ├── style.css
│   └── app.js
│

└── 📁 instance/                 # Base de données
    └── users.db                 # 
    
    

Demonstration : Captures d'ecran 

1/ Run Application :
 
<img width="1268" height="506" alt="pythonscreen1" src="https://github.com/user-attachments/assets/46a81729-5e07-4a04-a67f-fbff712a6b67" />

2/interface de connexion :


<img width="1289" height="666" alt="pythoscr2" src="https://github.com/user-attachments/assets/76434a3b-5027-4b46-aa76-6ef1e26b4aed" />

3/ dashboard pour user 1:

<img width="1289" height="666" alt="scrre3" src="https://github.com/user-attachments/assets/12da4792-d36c-4386-863d-610ea520f2a9" />

4/ dasboard pour user 2:

<img width="1289" height="666" alt="scrre4" src="https://github.com/user-attachments/assets/0f2160ba-465d-488c-9773-428f80d02ad7" />

