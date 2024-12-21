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

def analyser_code(outils, code, file_path):
    """Analyse code with specified tools and return results."""
    with tempfile.NamedTemporaryFile(delete=True, suffix=".py") as temp_file:
        temp_file.write(code.encode())
        temp_file.flush()  # Ensure the content is written to the file
        temp_file_path = temp_file.name

        results = {}
        for outil in outils:
            try:
                result = subprocess.run(outil + [temp_file_path], capture_output=True, text=True)
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

        # Write results to a text file
        with open(f"{file_path}_analysis_results.txt", "w", encoding="utf-8") as result_file:
            for tool, output in results.items():
                result_file.write(f"Results for {tool}:\n{output}\n\n")

        return results

def analyser_sonarqube(file_path):
    """Analyse code with SonarQube and return results."""
    sonar_url = "http://localhost:9000/api/qualitygates/project_status"
    sonar_token = "your_sonarqube_token"
    project_key = "your_project_key"

    with open("sonar-project.properties", "w") as f:
        f.write(f"sonar.projectKey={project_key}\n")
        f.write(f"sonar.sources={os.path.dirname(file_path)}\n")
        f.write("sonar.host.url=http://localhost:9000\n")
        f.write(f"sonar.login={sonar_token}\n")

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
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    outils = [["flake8"], ["pylint"]]
                    resultats = analyser_code(outils, code, file_path)
                    print(f"Résultats pour {file_path} : {resultats}")
    elif choix == 'non':
        choix = input("Voulez-vous analyser les fichiers depuis une URL ? (oui/non) : ").strip().lower()
        if choix == 'oui':
            url = input("Veuillez entrer l'URL du fichier à analyser : ")
            if not is_valid_url(url):
                logging.error(f"URL invalide : {url}")
                sys.exit(1)
            response = requests.get(url)
            if response.status_code != 200:
                logging.error(f"Erreur lors du téléchargement du fichier : {response.status_code}")
                sys.exit(1)
            code = response.text
            outils = [["flake8"], ["pylint"]]
            resultats = analyser_code(outils, code, "url_analysis")
            print(f"Résultats pour {url} : {resultats}")
        else:
            logging.info("Aucune analyse effectuée.")
            sys.exit(0)
    else:
        logging.error("Choix invalide. Veuillez répondre par 'oui' ou 'non'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
