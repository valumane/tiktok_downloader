import os
import sys
import json
import yt_dlp

def sanitize_filename(filename):
    """
    Nettoie le nom de fichier pour supprimer ou remplacer les caractères non valides.
    """
    return filename.replace(":", "").replace("/", "_").replace("?", "").replace("&", "").replace("=", "_")

def download_tiktok_content_from_file(json_file, output_dir):
    """
    Télécharge les vidéos TikTok depuis un fichier JSON contenant les URLs.

    Args:
        json_file (str): Chemin du fichier JSON contenant les URLs TikTok.
        output_dir (str): Répertoire de destination pour sauvegarder le contenu.
    """
    try:
        #charge le fichier JSON
        with open(json_file, "r", encoding="utf-8") as f:
            url_list = json.load(f)

        #creation du dossier des vidéos
        video_dir = os.path.join(output_dir, "videos")
        os.makedirs(video_dir, exist_ok=True)

        total_elements = len(url_list)  # Nombre total d'éléments

        #parcour de la liste des URLs
        for idx, url in enumerate(url_list, start=1):
            #verif si l'URL contient "photo"
            if "/photo/" in url:
                print(f"Rencontré une URL de photo : {url}. Arrêt du téléchargement.")
                break

            # Afficher la progression
            print(f"Téléchargement {idx}/{total_elements} : {url}")

            #nettoie l'URL pour l'utiliser comme nom de fichier
            sanitized_url = sanitize_filename(url)
            output_template = os.path.join(video_dir, f"{sanitized_url}.%(ext)s")

            #opt pour yt_dlp
            ydl_opts = {
                'outtmpl': output_template,
                'format': 'mp4',
                'quiet': True,  #enleve les messages inutiles
            }

            # telecharge le contenu
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)
                    print(f"Téléchargé avec succès : {info_dict.get('title', 'unknown')}")
            except Exception as e:
                print(f"Erreur lors du téléchargement de {url} : {e}")

    except FileNotFoundError:
        print(f"Erreur : Le fichier JSON '{json_file}' est introuvable.")
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier '{json_file}' n'est pas un JSON valide.")
    except Exception as e:
        print(f"Erreur générale : {e}")

# verif des arguments du script
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage : python tiktoksave.py <sorted_tiktok_link.json> <output_directory>")
        sys.exit(1)

    # recuper les arguments
    json_file = sys.argv[1]
    output_directory = sys.argv[2]

    # telecharge le contenu depuis le fichier JSON
    download_tiktok_content_from_file(json_file, output_directory)
