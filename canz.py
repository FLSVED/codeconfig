import os
import subprocess
import tempfile
import requests
from textblob import TextBlob
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

# Function to check if a tool is installed
def verifier_outil(outil):
    try:
        subprocess.run([outil, '--version'], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Function to analyze code with various tools
def analyser_code(outils, file_path):
    results = {}
    for outil in outils:
        if verifier_outil(outil[0]):
            try:
                result = subprocess.run(outil + [file_path], capture_output=True, text=True, check=True)
                results[outil[0]] = result.stdout
            except subprocess.CalledProcessError as e:
                results[outil[0]] = e.output
        else:
            results[outil[0]] = f"{outil[0]} n'est pas installé ou accessible."
    return results

# Function to check if a URL is valid
def is_valid_url(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Function to generate suggestions based on analysis results
def generer_suggestions(results):
    suggestions = []
    for outil, result in results.items():
        if "flake8" in outil:
            suggestions.append("Utilisez flake8 pour corriger les erreurs de style.")
        if "pylint" in outil:
            suggestions.append("Utilisez pylint pour améliorer la qualité du code.")
        if "textblob" in outil:
            suggestions.append("Utilisez TextBlob pour analyser les structures de texte.")
        if "bandit" in outil:
            suggestions.append("Utilisez bandit pour analyser les vulnérabilités de sécurité.")
        if "mypy" in outil:
            suggestions.append("Utilisez mypy pour vérifier les annotations de type.")
        if "black" in outil:
            suggestions.append("Utilisez black pour formater le code.")
        if "isort" in outil:
            suggestions.append("Utilisez isort pour trier les imports.")
        if "pydocstyle" in outil:
            suggestions.append("Utilisez pydocstyle pour vérifier les docstrings.")
        if "coverage" in outil:
            suggestions.append("Utilisez coverage pour mesurer la couverture des tests.")
        if "xenon" in outil:
            suggestions.append("Utilisez xenon pour analyser la complexité du code.")
    return sorted(list(set(suggestions)))  # Remove duplicates and sort

# Function to apply corrections to the code
def appliquer_corrections(code, results):
    corrected_code = code
    for outil, result in results.items():
        if "flake8" in outil:
            # Apply flake8 corrections
            pass
        if "pylint" in outil:
            # Apply pylint corrections
            pass
        if "textblob" in outil:
            # Apply TextBlob corrections
            pass
        if "black" in outil:
            # Apply black corrections
            pass
        if "isort" in outil:
            # Apply isort corrections
            pass
    return corrected_code

# Function to write results to a file
def ecrire_resultats_dans_fichier(filepath, results, suggestions):
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            for outil, result in results.items():
                file.write(f"Résultats de l'analyse avec {outil}:\n{result}\n\n")
            file.write("Suggestions de correction:\n")
            for suggestion in suggestions:
                file.write(f"- {suggestion}\n")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture des résultats dans le fichier {filepath} : {e}")
        raise

def main():
    choix = input("Voulez-vous analyser les fichiers depuis un répertoire local ? (oui/non) : ").strip().lower()
    if choix == 'oui':
        path = demander_acces_aux_fichiers()
        for root, dirs, files in os.walk(path):
            for filename in files:
                if filename.endswith('.py'):
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        code = file.read()
                    outils = [["flake8"], ["pylint"], ["textblob"], ["bandit"], ["mypy"], ["black"], ["isort"], ["pydocstyle"], ["coverage"], ["xenon"]]
                    results = analyser_code(outils, file_path)
                    suggestions = generer_suggestions(results)
                    corrected_code = appliquer_corrections(code, results)
                    print(f"Résultats pour {file_path} : {results}")
                    print(f"Suggestions : {suggestions}")
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(corrected_code)
                    ecrire_resultats_dans_fichier("resultats_analyse.txt", results, suggestions)
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
            outils = [["flake8"], ["pylint"], ["textblob"], ["bandit"], ["mypy"], ["black"], ["isort"], ["pydocstyle"], ["coverage"], ["xenon"]]
            with tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w', encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            try:
                results = analyser_code(outils, temp_file_path)
                suggestions = generer_suggestions(results)
                corrected_code = appliquer_corrections(code, results)
                print(f"Résultats pour {url} : {results}")
                print(f"Suggestions : {suggestions}")
                with open(temp_file_path, 'w', encoding='utf-8') as file:
                    file.write(corrected_code)
                ecrire_resultats_dans_fichier("resultats_analyse.txt", results, suggestions)
            finally:
                os.remove(temp_file_path)
        else:
            logging.info("Aucune analyse effectuée.")
            sys.exit(0)
    else:
        logging.error("Choix invalide. Veuillez répondre par 'oui' ou 'non'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
