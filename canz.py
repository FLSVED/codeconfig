import logging
import os
import subprocess
import sys
import tempfile
import requests
import asyncio
import argparse
from typing import List

# Configuration du logging avec différents niveaux
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Liste des outils d'analyse
TOOLS = [
    ["flake8"],
    ["pylint"],
    ["bandit"],
    ["mypy"],
    ["black"],
    ["isort"],
    ["pydocstyle"],
    ["coverage"],
    ["xenon"],
    ["vulture"],
    ["pyflakes"],
    ["pyright"],
    ["pyre"],
    ["safety"],
    ["prospector"],
    ["trufflehog"],
    ["radon", "cc", "-a"],  # Pour analyser la complexité cyclomatique
]

class ToolNotFoundError(Exception):
    """Exception levée lorsque l'outil n'est pas trouvé."""
    pass

class AnalysisError(Exception):
    """Exception levée en cas d'erreur d'analyse."""
    pass

def verifier_outil(outil: str) -> bool:
    """Vérifie si un outil est installé."""
    try:
        subprocess.run([outil, '--version'], capture_output=True, text=True, check=True)
        return True
    except FileNotFoundError:
        logging.error(f"L'outil {outil} n'est pas installé.")
        raise ToolNotFoundError(f"{outil} n'est pas trouvé.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'exécution de {outil} : {e}")
        raise AnalysisError(f"Échec de l'exécution de {outil}.")

async def analyser_code(outils: List[List[str]], file_path: str) -> dict:
    """Analyse le code avec les outils spécifiés."""
    results = {}
    for outil in outils:
        try:
            if verifier_outil(outil[0]):
                result = subprocess.run(outil + [file_path], capture_output=True, text=True, check=True)
                results[outil[0]] = result.stdout
        except (ToolNotFoundError, AnalysisError) as e:
            results[outil[0]] = str(e)
    return results

def generer_suggestions(results: dict) -> List[str]:
    """Génère des suggestions de correction basées sur les résultats des outils."""
    suggestions = []
    for outil, result in results.items():
        if "flake8" in outil and "E" in result:
            suggestions.append("Utilisez flake8 pour corriger les erreurs de style.")
        if "pylint" in outil and "E" in result:
            suggestions.append("Utilisez pylint pour améliorer la qualité du code.")
        if "bandit" in outil and "issue" in result:
            suggestions.append("Utilisez bandit pour analyser les vulnérabilités de sécurité.")
        if "mypy" in outil and "error" in result:
            suggestions.append("Utilisez mypy pour vérifier et corriger les annotations de type.")
        if "safety" in outil and "vulnerability" in result:
            suggestions.append("Utilisez safety pour mettre à jour les dépendances.")
        if "radon" in outil and "Complexity" in result:
            suggestions.append("Utilisez radon pour réduire la complexité cyclomatique.")
    return sorted(list(set(suggestions)))

def handle_syntax_errors(results: dict) -> bool:
    """Vérifie s'il y a des erreurs de syntaxe dans le code."""
    for outil, result in results.items():
        if "SyntaxError" in result or "invalid syntax" in result:
            return True
    return False

def appliquer_corrections(code: str, results: dict, file_path: str) -> str:
    """Applique des corrections automatiques au code."""
    if handle_syntax_errors(results):
        logging.error("Le code contient des erreurs de syntaxe.")
        return code
    corrected_code = code
    for outil in ["black", "isort"]:
        if outil in results:
            try:
                logging.info(f"Application de {outil} pour formater le code.")
                subprocess.run([outil, file_path], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Erreur lors de l'application de {outil} : {e}")
    return corrected_code

def ecrire_resultats_dans_fichier(filepath: str, results: dict, suggestions: List[str]):
    """Écrit les résultats de l'analyse et les suggestions dans un fichier."""
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

def ecrire_code_dans_fichier(filepath: str, code: str):
    """Écrit le code dans un fichier."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(code)
    except Exception as e:
        logging.error("Erreur lors de l'écriture du code dans le fichier %s : %s", filepath, e)
        raise

def is_valid_url(url: str) -> bool:
    """Vérifie si une URL est valide."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error("Erreur lors de la vérification de l'URL : %s", e)
        return False

async def analyser_fichier_url(url: str, outils: List[List[str]]):
    """Analyse un fichier Python provenant d'une URL."""
    if not is_valid_url(url):
        logging.error("URL invalide : %s", url)
        sys.exit(1)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error("Erreur lors du téléchargement du fichier : %s", e)
        sys.exit(1)
    code = response.text
    with tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    try:
        results = await analyser_code(outils, temp_file_path)
        suggestions = generer_suggestions(results)
        corrected_code = appliquer_corrections(code, results, temp_file_path)
        print(f"Résultats pour {url} : {results}")
        print(f"Suggestions : {suggestions}")
        if corrected_code != code:
            with open(temp_file_path, 'w', encoding='utf-8') as file:
                file.write(corrected_code)
        ecrire_resultats_dans_fichier(f"resultats_{os.path.basename(url)}.txt", results, suggestions)
        ecrire_code_dans_fichier("code_complet.txt", code)
    finally:
        os.remove(temp_file_path)

async def analyser_fichier_local(path: str, outils: List[List[str]]):
    """Analyse les fichiers Python dans un répertoire local."""
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.endswith('.py'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    code = file.read()
                results = await analyser_code(outils, file_path)
                suggestions = generer_suggestions(results)
                corrected_code = appliquer_corrections(code, results, file_path)
                print(f"Résultats pour {file_path} : {results}")
                print(f"Suggestions : {suggestions}")
                if corrected_code != code:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(corrected_code)
                ecrire_resultats_dans_fichier(f"resultats_{filename}.txt", results, suggestions)
                ecrire_code_dans_fichier("code_complet.txt", code)

def parse_arguments():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description="Analyseur de code Python avec divers outils.")
    parser.add_argument('--local', type=str, help='Chemin du répertoire local à analyser.')
    parser.add_argument('--url', type=str, help='URL du fichier à analyser.')
    return parser.parse_args()

async def main():
    """Point d'entrée principal du programme."""
    args = parse_arguments()
    outils_a_utiliser = TOOLS  # Ici, pour simplifier, on utilise tous les outils
    if args.local:
        await analyser_fichier_local(args.local, outils_a_utiliser)
    elif args.url:
        await analyser_fichier_url(args.url, outils_a_utiliser)
    else:
        logging.error("Veuillez spécifier un répertoire local ou une URL pour l'analyse.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```
