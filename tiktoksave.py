import yt_dlp

def sanitize_filename(filename):
    return filename.replace(":", "").replace("/", "_").replace("?", "").replace("&", "").replace("=", "_")

def download_tiktok_video(video_url, output_dir):
    try:
        # Nettoyer l'URL pour l'utiliser comme nom de fichier
        sanitized_url = sanitize_filename(video_url)
        output_template = f"{output_dir}\\{sanitized_url}.%(ext)s"

        ydl_opts = {
            'outtmpl': output_template,
            'format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            print(f"Downloaded video: {output_template}")
    except Exception as e:
        print("Error:", str(e))

# Example usage
if __name__ == "__main__":
    tiktok_url = ""
    download_directory = ""
    download_tiktok_video(tiktok_url, download_directory)
