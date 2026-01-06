import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'users.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Docker settings
    DOCKER_BASE_URL = os.environ.get('DOCKER_BASE_URL') or 'unix:///var/run/docker.sock'
    NGINX_IMAGE = 'nginx:alpine'
    CONTAINER_PREFIX = 'user'
    
    # Port range for user containers
    PORT_RANGE_START = 8000
    PORT_RANGE_END = 8999
