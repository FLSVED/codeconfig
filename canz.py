import os
import subprocess
import tempfile
import git  # Ensure GitPython is installed with `pip install GitPython`
from textblob import TextBlob
import requests
from urllib.parse import urlparse

def analyser_code(outils, code):
    """Analyse code with specified tools and return results."""
    with tempfile.NamedTemporaryFile(delete=True, suffix=".py") as temp_file:
        temp_file.write(code.encode())
        temp_file_path = temp_file.name

    results = {}
    for outil in outils:
        try:
            result = subprocess.run(outil + [temp_file_path], capture_output=True, text=True, check=True)
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

    subprocess.run(["sonar-scanner", f"-Dsonar.projectKey={project_key}", f"-Dsonar.sources={file_path}"])

    if not is_valid_url(sonar_url):
        raise Exception(f"Invalid URL: {sonar_url}")

    response = requests.get(sonar_url, auth=(sonar_token, ''))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"SonarQube analysis failed with status code {response.status_code}")

def is_valid_url(url):
    """Validate a URL."""
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme) and bool(parsed_url.netloc)

def evaluer_suggestion(code):
    """Evaluate sentiment of a code suggestion."""
    blob = TextBlob(code)
    return blob.sentiment.polarity

def evaluer_clarte(code):
    """Evaluate code clarity based on number of lines."""
    return len(code.splitlines())  # More lines, less clear

def evaluer_erreurs(code):
    """Evaluate number of errors in the code."""
    error_count = 0
    if "print" not in code:
        error_count += 1
    return error_count

def generer_suggestions(problemes):
    """Generate improvement suggestions based on detected issues."""
    suggestions = []
    if 'E1101' in problemes:  # Pylint error for undefined variable use
        suggestions.append("Ensure all variables are defined before use.")
    if 'F401' in problemes:  # Flake8 for unused import
        suggestions.append("Remove unused imports.")
    if 'sonarqube' in problemes:
        suggestions.append("Check SonarQube results for detailed suggestions.")
    if 'Outil introuvable' in problemes:
        suggestions.append("Ensure all analysis tools are installed and accessible.")
    return suggestions

def choisir_meilleure_suggestion(suggestions):
    """Choose the best suggestion among those provided."""
    scores = {}
    for suggestion in suggestions:
        clarity = evaluer_clarte(suggestion)
        errors = evaluer_erreurs(suggestion)
        sentiment = evaluer_suggestion(suggestion)
        score = sentiment - errors - (clarity / 10)
        scores[suggestion] = score

    meilleur_code = max(scores, key=scores.get)
    return meilleur_code

def lire_code_depuis_fichier(nom_fichier):
    """Read code from a given file."""
    with open(nom_fichier, 'r') as f:
        return f.read()

def ecrire_resultats_dans_fichier(nom_fichier, resultats):
    """Write analysis results and suggestions to a single file."""
    with open(nom_fichier, 'w') as f:
        f.write("Analysis Report and Improvement Suggestions\n")
        f.write("=" * 50 + "\n\n")
        for fichier, details in resultats.items():
            f.write(f"File: {fichier}\n")
            f.write("-" * 50 + "\n")
            f.write("Best suggestion:\n")
            f.write(details['meilleure_suggestion'] + "\n\n")
            f.write("Suggestions for improvement:\n")
            for suggestion in details['suggestions']:
                f.write("- " + suggestion + "\n")
            f.write("\n")

        # Additional suggestions specific to canz.py
        f.write("File: canz.py\n")
        f.write("Best suggestion:\n\n")
        f.write("Suggestions for improvement:\n")
        f.write("- Check SonarQube results for detailed suggestions.\n")
        f.write("- Ensure all analysis tools are installed and accessible.\n")
        f.write("\n")

def sauvegarder_code_et_architecture(path, nom_fichier):
    """Save all code from all modules into a single text file with the complete architecture."""
    with open(nom_fichier, 'w') as f:
        f.write("Code Architecture\n")
        f.write("=" * 50 + "\n\n")
        
        for root, dirs, files in os.walk(path):
            for filename in files:
                if filename.endswith('.py'):
                    full_path = os.path.join(root, filename)
                    f.write(f"Module: {full_path}\n")
                    f.write("-" * 50 + "\n")
                    with open(full_path, 'r') as code_file:
                        f.write(code_file.read())
                    f.write("\n\n")

def generer_prompts_pour_copilote(resultats_analyse):
    """Generate a file of prompts for Copilot based on analysis results and suggestions."""
    prompts = []
    for fichier, details in resultats_analyse.items():
        prompts.append(f"File: {fichier}")
        prompts.append("Best suggestion:")
        prompts.append(details['meilleure_suggestion'])
        prompts.append("Suggestions for improvement:")
        for suggestion in details['suggestions']:
            prompts.append("- " + suggestion)
        prompts.append("\n")

    chemin_prompts = os.path.join(os.path.dirname(__file__), "prompt.txt")
    with open(chemin_prompts, 'w') as f:
        f.write("\n".join(prompts))
    print(f"Prompt file generated: {chemin_prompts}")

def analyser_modules(path):
    """Analyze all Python files in a given directory and save the code and architecture."""
    resultats_analyse = {}
    
    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a valid directory.")
        return

    outils = [
        ['pylint'],
        ['flake8'],
        ['bandit', '-r'],
        ['mypy'],
        ['black', '--check'],
        ['isort', '--check'],
        ['pydocstyle'],
        ['coverage', 'run'],
        ['radon', 'cc']
    ]

    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.endswith('.py'):
                full_path = os.path.join(root, filename)
                print(f"Analyzing file: {full_path}")
                
                try:
                    code_a_corriger = lire_code_depuis_fichier(full_path)

                    # Analysis with various tools
                    results = analyser_code(outils, code_a_corriger)

                    # Generate suggestions based on problems
                    suggestions = generer_suggestions(results)
                    meilleure_suggestion = choisir_meilleure_suggestion(suggestions)

                    resultats_analyse[filename] = {
                        'meilleure_suggestion': meilleure_suggestion,
                        'suggestions': suggestions
                    }
                except Exception as e:
                    print(f"Error analyzing file '{full_path}': {e}")

    # Save analysis results
    ecrire_resultats_dans_fichier("analysis_results.txt", resultats_analyse)
    sauvegarder_code_et_architecture(path, "complete_code.txt")
    generer_prompts_pour_copilote(resultats_analyse)
