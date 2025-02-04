import requests
import os
import re

# Variable untuk konfigurasi
GRAFANA_URL = os.getenv("GRAFANA_URL")
API_KEY = os.getenv("API_KEY")
OUTPUT_DIR = "grafana_backup"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Buat folder root jika belum ada
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_all_folders_and_dashboards():
    # Mengambil semua folder dan dashboard dari Grafana
    response = requests.get(f"{GRAFANA_URL}/api/search?type=dash-folder", headers=HEADERS)
    response.raise_for_status()
    folders = response.json()

    # Mengambil semua dashboard tanpa folder (di General)
    response_dashboards = requests.get(f"{GRAFANA_URL}/api/search?type=dash-db", headers=HEADERS)
    response_dashboards.raise_for_status()
    dashboards = response_dashboards.json()
    return folders, dashboards

def get_dashboards_in_folder(folder_id):
    # Mengambil semua dashboard dalam folder tertentu
    response = requests.get(f"{GRAFANA_URL}/api/search?folderIds={folder_id}&type=dash-db", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_folder_path(folder, folders_dict):
    # Menghasilkan jalur folder lengkap berdasarkan hierarki folderTitle.
    path_parts = []

    # Loop untuk membangun jalur dari parent ke child
    while folder:
        path_parts.append(folder["title"])
        parent_title = folder.get("folderTitle")
        if parent_title:
            # Cari parent folder berdasarkan folderTitle
            folder = next((f for f in folders_dict.values() if f["title"] == parent_title), None)
        else:
            break

    # Bangun jalur folder dari root ke anak
    path_parts.reverse()
    folder_path = os.path.join(*path_parts)

    # Sanitasi jalur folder untuk menghindari karakter ilegal
    sanitized_folder_path = re.sub(r'[\\:*?"<>|]', "_", folder_path)
    return sanitized_folder_path

def backup_dashboard(folder_path, uid, title):
    # Backup dashboard berdasarkan UID dan menyimpannya di folder lokal
    response = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{uid}", headers=HEADERS)
    response.raise_for_status()

    # Sanitasi nama file
    sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", title)  # Ganti karakter ilegal pada nama file

    # Buat folder lokal untuk backup
    full_folder_path = os.path.join(OUTPUT_DIR, folder_path)  # Gabungkan jalur folder dengan root
    os.makedirs(full_folder_path, exist_ok=True)  # Buat folder sesuai hierarki

    # Simpan file JSON di folder yang sesuai
    file_path = os.path.join(full_folder_path, f"{sanitized_title}.json")  # File hanya di dalam folder target
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"Dashboard '{title}' berhasil dibackup ke: {file_path}")

def main():
    print("Mengambil daftar semua folder dan dashboard...")
    folders, general_dashboards = get_all_folders_and_dashboards()

    # Buat dictionary untuk semua folder dengan title sebagai kunci
    folders_dict = {folder["title"]: folder for folder in folders}

    # Backup dashboard tanpa folder (General)
    if general_dashboards:
        print(f"\nMemproses dashboard di folder General (tanpa folder):")
        for dashboard in general_dashboards:
            # Validasi apakah dashboard memiliki key 'folderId'
            if "folderId" in dashboard:
                continue  # Skip jika dashboard memiliki folderId
            uid = dashboard["uid"]
            title = dashboard["title"]
            backup_dashboard("General", uid, title)

    # Backup dashboard dalam folder
    print(f"\nTotal folder ditemukan: {len(folders)}")
    for folder in folders:
        folder_id = folder["id"]
        folder_title = folder["title"]

        # Tentukan jalur folder
        folder_path = get_folder_path(folder, folders_dict)
        print(f"\nMemproses folder: {folder_title} (ID: {folder_id})")

        # Dapatkan semua dashboard dalam folder
        dashboards = get_dashboards_in_folder(folder_id)
        print(f"  Total dashboard di folder '{folder_title}': {len(dashboards)}")

        for dashboard in dashboards:
            uid = dashboard["uid"]
            title = dashboard["title"]
            backup_dashboard(folder_path, uid, title)

    print("\nSemua folder dan dashboard berhasil dibackup!")

if __name__ == "__main__":
    main()
