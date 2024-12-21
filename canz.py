import logging
import os
import subprocess
import sys
import tempfile
import requests

TOOLS = [
    ["flake8"],
    ["pylint"],
    ["textblob"],
    ["bandit"],
    ["mypy"],
    ["black"],
    ["isort"],
    ["pydocstyle"],
    ["coverage"],
    ["xenon"],
]
RESULTS_FILE = "resultats_analyse.txt"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def demander_acces_aux_fichiers():
    try:
        path = input("Veuillez entrer le chemin du répertoire à analyser : ")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Le chemin spécifié n'existe pas : {path}")
        return path
    except FileNotFoundError as e:
        logging.error("Erreur lors de la demande d'accès aux fichiers : %s", e)
        sys.exit(1)
    except Exception as e:
        logging.error("Erreur inattendue : %s", e)
        sys.exit(1)

def verifier_outil(outil):
    try:
        subprocess.run([outil, '--version'], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def verifier_tous_les_outils(outils):
    for outil in outils:
        if not verifier_outil(outil[0]):
            logging.error(f"L'outil {outil[0]} n'est pas installé.")
            sys.exit(1)

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

def is_valid_url(url):
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error("Erreur lors de la vérification de l'URL : %s", e)
        return False

def generer_suggestions(results):
    suggestions = []
    for outil, result in results.items():
        if "flake8" in outil and "E" in result:
            suggestions.append("Utilisez flake8 pour corriger les erreurs de style.")
        if "pylint" in outil and "E" in result:
            suggestions.append("Utilisez pylint pour améliorer la qualité du code.")
        if "textblob" in outil:
            suggestions.append("Utilisez TextBlob pour analyser les structures de texte.")
        if "bandit" in outil and "issue" in result:
            suggestions.append("Utilisez bandit pour analyser les vulnérabilités de sécurité.")
        if "mypy" in outil and "error" in result:
            suggestions.append("Utilisez mypy pour vérifier les annotations de type.")
        if "black" in outil:
            suggestions.append("Utilisez black pour formater le code.")
        if "isort" en outil:
            suggestions.append("Utilisez isort pour trier les imports.")
        if "pydocstyle" en outil:
            suggestions.append("Utilisez pydocstyle pour vérifier les docstrings.")
        if "coverage" en outil:
            suggestions.append("Utilisez coverage pour mesurer la couverture des tests.")
        if "xenon" en outil:
            suggestions.append("Utilisez xenon pour analyser la complexité du code.")
    return sorted(list(set(suggestions)))

def appliquer_corrections(code, results):
    corrected_code = code
    for outil, result in results.items():
        if "flake8" in outil:
            pass
        if "pylint" en outil:
            pass
        if "textblob" en outil:
            pass
        if "black" en outil:
            pass
        if "isort" en outil:
            pass
    return corrected_code

def ecrire_resultats_dans_fichier(filepath, results, suggestions):
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            for outil, result in results.items():
                file.write(f"Résultats de l'analyse avec {outil}:\n{result}\n\n")
            file.write("Suggestions de correction:\n")
            for suggestion in suggestions:
                file.write(f"- {suggestion}\n")
    except Exception as e:
        logging.error("Erreur lors de l'écriture des résultats dans le fichier %s : %s", filepath, e)
        raise

def analyser_fichier_local(path):
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.endswith('.py'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    code = file.read()
                results = analyser_code(TOOLS, file_path)
                suggestions = generer_suggestions(results)
                corrected_code = appliquer_corrections(code, results)
                print(f"Résultats pour {file_path} : {results}")
                print(f"Suggestions : {suggestions}")
                if corrected_code != code:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(corrected_code)
                ecrire_resultats_dans_fichier(RESULTS_FILE, results, suggestions)

def analyser_fichier_url(url):
    if not is_valid_url(url):
        logging.error("URL invalide : %s", url)
        sys.exit(1)
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        logging.error("Erreur lors du téléchargement du fichier : %s", response.status_code)
        sys.exit(1)
    code = response.text
    with tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    try:
        results = analyser_code(TOOLS, temp_file_path)
        suggestions = generer_suggestions(results)
        corrected_code = appliquer_corrections(code, results)
        print(f"Résultats pour {url} : {results}")
        print(f"Suggestions : {suggestions}")
        if corrected_code != code:
            with open(temp_file_path, 'w', encoding='utf-8') as file:
                file.write(corrected_code)
        ecrire_resultats_dans_fichier(RESULTS_FILE, results, suggestions)
    finally:
        os.remove(temp_file_path)

def main():
    choix = input("Voulez-vous analyser les fichiers depuis un répertoire local ? (oui/non) : ").strip().lower()
    if choix == 'oui':
        path = demander_acces_aux_fichiers()
        analyser_fichier_local(path)
    elif choix == 'non':
        choix = input("Voulez-vous analyser les fichiers depuis une URL ? (oui/non) : ").strip().lower()
        if choix == 'oui':
            url = input("Veuillez entrer l'URL du fichier à analyser : ")
            analyser_fichier_url(url)
        else:
            logging.info("Aucune analyse effectuée.")
            sys.exit(0)
    else:
        logging.error("Choix invalide. Veuillez répondre par 'oui' ou 'non'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
