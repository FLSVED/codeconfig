import os
import subprocess
import tempfile
import git  # Ensure GitPython is installed with `pip install GitPython`
from textblob import TextBlob
import requests
from urllib.parse import urlparse
import logging
import sys

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize resultats_analyse as an empty dictionary
resultats_analyse = {}

# Function to request access to local files
def demander_acces_aux_fichiers():
    try:
        path = input("Veuillez entrer le chemin du répertoire à analyser : ")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Le chemin spécifié n'existe pas : {path}")
        return path
    except Exception as e:
        logging.error(f"Erreur lors de la demande d'accès aux fichiers : {e}")
        sys.exit(1)

def analyser_code(outils, code):
    """Analyse code with specified tools and return results."""
    with tempfile.NamedTemporaryFile(delete=True, suffix=".py") as temp_file:
        temp_file.write(code.encode())
        temp_file_path = temp_file.name

        results = {}
        for outil in outils:
            try:
                result = subprocess.run(outil, capture_output=True, text=True)
                results[outil[0]] = result.stdout
            except subprocess.CalledProcessError as e:
                results[outil[0]] = f"Error running {outil[0]}: {e}"
            except FileNotFoundError:
                results[outil[0]] = f"Error {outil[0]}: Tool not found"
            except Exception as e:
                results[outil[0]] = f"Error {outil[0]}: {e}"

        # SonarQube Analysis
        try:
            sonar_result = analyser_sonarqube(temp_file_path)
            results['sonarqube'] = sonar_result
        except Exception as e:
            results['sonarqube'] = f"SonarQube Error: {e}"

        return results

def analyser_sonarqube(file_path):
    """Analyse code with SonarQube and return results."""
    sonar_url = "http://localhost:9000/api/qualitygates/project_status"
    sonar_token = "your_sonarqube_token"
    project_key = "your_project_key"

    with open("sonar-project.properties", "w") as f:
        f.write("sonar.projectKey=my_project\n")
        f.write("sonar.sources=.\n")
        f.write("sonar.host.url=http://localhost:9000\n")
        f.write("sonar.login=your_sonarqube_token\n")

    subprocess.run(["sonar-scanner"])

    if not is_valid_url(sonar_url):
        raise Exception(f"Invalid URL: {sonar_url}")

    response = requests.get(sonar_url, auth=(sonar_token, ''))
    if response.status_code != 200:
        raise Exception(f"SonarQube API request failed with status code {response.status_code}")

    return response.json()

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def main():
    choix = input("Voulez-vous analyser les fichiers depuis un répertoire local ? (oui/non) : ").strip().lower()
    if choix == 'oui':
        path = demander_acces_aux_fichiers()
        # Analyse des fichiers dans le répertoire local
        # ...
    elif choix == 'non':
        choix = input("Voulez-vous analyser les fichiers depuis une URL ? (oui/non) : ").strip().lower()
        if choix == 'oui':
            url = input("Veuillez entrer l'URL du fichier à analyser : ")
            if not is_valid_url(url):
                logging.error(f"URL invalide : {url}")
                sys.exit(1)
            # Téléchargement et analyse des fichiers depuis l'URL
            # ...
        else:
            logging.info("Aucune analyse effectuée.")
            sys.exit(0)
    else:
        logging.error("Choix invalide. Veuillez répondre par 'oui' ou 'non'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
