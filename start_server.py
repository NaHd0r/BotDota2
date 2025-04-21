"""
Script pour démarrer le serveur sur un port disponible
"""
import os
import socket
import sys
import subprocess

def is_port_in_use(port):
    """Vérifie si un port est déjà utilisé"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=5000, max_attempts=10):
    """Trouve un port disponible en commençant par start_port"""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"Impossible de trouver un port disponible après {max_attempts} tentatives")

def start_server():
    """Démarre le serveur gunicorn sur un port disponible"""
    try:
        # Commencer par le port 5000
        port = find_available_port(5000)
        print(f"Démarrage du serveur sur le port {port}")
        
        # Démarrer gunicorn avec le port disponible
        cmd = ["gunicorn", "--bind", f"0.0.0.0:{port}", "--reuse-port", "--reload", "main:app"]
        subprocess.run(cmd)
    except Exception as e:
        print(f"Erreur lors du démarrage du serveur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()