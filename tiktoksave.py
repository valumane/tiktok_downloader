# tiktoksave.py

import os
import sys
import json
import time
import yt_dlp
import argparse
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO

# === UTILS ===
def sanitize_filename(filename):
    safe = filename.replace("/", "_").replace("\\", "_").replace("|", "_")
    safe = safe.replace(":", "_").replace("?", "").replace("*", "_").replace("\"", "")
    safe = safe.replace("<", "").replace(">", "").replace("&", "et").replace("#", "")
    safe = safe.replace("\n", " ").replace("\r", " ").strip()
    return safe[:150]  # encore plus safe

def log_message(log_path, message):
    with open(log_path, "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log_file.write(f"{timestamp} {message}\n")

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--enable-unsafe-swiftshader")
    return webdriver.Chrome(options=options)

# === CAROUSEL IMAGE DOWNLOAD ===
def download_carousel_images(tiktok_url, output_root):
    driver = setup_driver()
    try:
        print(f"🔍 Chargement de la page : {tiktok_url}")
        driver.get(tiktok_url)
        time.sleep(5)

        title = None
        try:
            for _ in range(2):
                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, 'h1[data-e2e="browse-video-title"]')
                    title = sanitize_filename(title_element.text)
                    if title:
                        break
                except:
                    time.sleep(1)
        except Exception as e:
            print(f"⚠️ Impossible de récupérer le titre proprement : {e}")

        if not title:
            title = "carrousel_" + tiktok_url.split("/")[-1]

        output_folder = os.path.join(output_root, title)
        os.makedirs(output_folder, exist_ok=True)

        images = driver.find_elements(By.TAG_NAME, "img")
        img_seen = set()
        img_index = 1
        for img in images:
            src = img.get_attribute("src")
            if src and "data:image" not in src and src not in img_seen:
                img_seen.add(src)
                filename = os.path.join(output_folder, f"image_{img_index}.jpg")
                try:
                    response = requests.get(src)
                    image = Image.open(BytesIO(response.content))
                    image.save(filename)
                    print(f"✅ Image sauvegardée : {filename}")
                    img_index += 1
                except Exception as e:
                    print(f"❌ Erreur image : {src} -> {e}")

        print(f"📁 Carrousel terminé : {title} ({img_index-1} images)")
        return title

    except Exception as e:
        print(f"❌ Erreur carrousel : {e}")
    finally:
        driver.quit()

# === AUDIO FROM PHOTO (smart fallback) ===
def get_music_url_from_carousel(photo_url):
    driver = setup_driver()
    try:
        driver.get(photo_url)
        time.sleep(5)
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and "/music/" in href:
                return href
        return None
    except Exception:
        return None
    finally:
        driver.quit()

def find_video_using_music(music_url):
    driver = setup_driver()
    try:
        driver.get(music_url)
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        links = [link.get_attribute("href") for link in driver.find_elements(By.TAG_NAME, "a") if link.get_attribute("href") and "/video/" in link.get_attribute("href")]
        return links
    except Exception:
        return []
    finally:
        driver.quit()

def download_audio_from_video(video_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = sanitize_filename(info.get("title", "musique"))

        output_path = os.path.join(output_dir, f"musique.mp3")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        print(f"✅ Audio depuis fallback : {output_path}")

    except Exception as e:
        print(f"❌ Erreur audio fallback : {e}")
        raise e

# === MAIN CONTROLLER ===
def download_tiktok_content(json_file, _):
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    output_dir = os.path.join(os.getcwd(), base_name)
    os.makedirs(output_dir, exist_ok=True)

    with open(json_file, "r", encoding="utf-8") as f:
        url_list = json.load(f)

    video_dir = os.path.join(output_dir, "videos")
    carousel_dir = os.path.join(output_dir, "carousels")
    log_path = os.path.join(output_dir, "download_log.txt")
    failed_path = os.path.join(output_dir, "failed_downloads.txt")

    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(carousel_dir, exist_ok=True)

    for idx, url in enumerate(url_list, start=1):
        print(f"\n📅 {idx}/{len(url_list)} : {url}")

        try:
            if "/photo/" in url:
                print("📸 Traitement d'un carrousel photo...")
                title = download_carousel_images(url, carousel_dir)
                carousel_path = os.path.join(carousel_dir, title)

                music_url = get_music_url_from_carousel(url)
                if music_url:
                    video_candidates = find_video_using_music(music_url)
                    for fallback_index, video_fallback in enumerate(video_candidates):
                        try:
                            print(f"🎧 Tentative audio via fallback n°{fallback_index + 1}")
                            download_audio_from_video(video_fallback, output_dir=carousel_path)
                            break
                        except Exception:
                            continue
                    else:
                        print("❌ Échec : aucune vidéo n'a permis d'extraire la musique.")
                else:
                    print("❌ Aucun son détecté sur le carrousel.")
                log_message(log_path, f"Carrousel traité : {url}")

            else:
                retry_success = False
                for attempt in range(2):
                    try:
                        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                            info = ydl.extract_info(url, download=False)
                            title = sanitize_filename(info.get("title", f"video_{idx}"))

                        video_output = os.path.join(video_dir, f"{title}.mp4")
                        ydl_opts_video = {
                            'outtmpl': video_output,
                            'format': 'mp4',
                            'quiet': True,
                        }

                        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                            ydl.download([url])

                        print(f"✅ Vidéo extraite : {title}")
                        log_message(log_path, f"Vidéo : {title} ({url})")
                        retry_success = True
                        break
                    except Exception as e:
                        print(f"⚠️ Erreur tentative {attempt + 1} : {e}")

                if not retry_success:
                    raise Exception("Échec après 2 tentatives")

        except Exception as e:
            print(f"❌ Erreur : {e}")
            log_message(log_path, f"Erreur : {url} - {e}")
            log_message(failed_path, url)

# === ENTRYPOINT ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Télécharge vidéos, musiques et carrousels TikTok depuis un JSON.")
    parser.add_argument("json_file", help="Chemin du fichier JSON contenant les URLs TikTok.")
    parser.add_argument("output_dir", help="Répertoire de sortie.")
    args = parser.parse_args()

    download_tiktok_content(args.json_file, args.output_dir)
