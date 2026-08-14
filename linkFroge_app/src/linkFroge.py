"""
This module contains the code to create a linkFroge link for the local server.
It uses the linkFroge API to create a link and returns the link to the user.
It also checks if ngrok is installed and downloads it if necessary.
"""

import io
import os
import zipfile
from pathlib import Path
import argparse
import subprocess
import requests
from tqdm import tqdm
import json
import sys
import time
import platform

# Directory where ngrok will be stored
ngpath = Path.home() / ".linkfroge"

# ngrok executable name
ngrok_executable = "ngrok.exe" if platform.system() == "Windows" else "ngrok"


def get_platform():
    """Determine the platform for downloading ngrok."""
    plat = platform.system()
    if plat == "Windows":
        return "windows-amd64"
    elif plat == "Linux":
        return "linux-amd64"
    elif plat == "Darwin":
        return "darwin-amd64"
    else:
        raise Exception("Unsupported platform")

plat = get_platform()


config = {
    "ngpath": str(ngpath),
    "verbose": False,
    "port": 55555,
    "linkfroge_api": "https://linkfroge.pythonanywhere.com/api",
    "localng-api": "http://127.0.0.1:4040/api/tunnels",
    "service-id": None,
    "Register-service-id": False,
    "service-token": None,
    "config_file": str(ngpath / "ngrok.yml"),
    "ng-auth-token": None,
    "download-ngrok": f"https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-{plat}.zip",
}


onStartInfo = {
    "service_id": None,
    "service_token": None,
    "service_link": None,
    "args": {}
}

# ============ Verbose logging helper ============
def vprint(*args, **kwargs):
    """Print only if verbose mode is enabled."""
    if config.get("verbose", False):
        print(*args, **kwargs)

def vprint_request(method, url, headers=None, body=None, response=None):
    """Pretty-print an API request/response in verbose mode."""
    if not config.get("verbose", False):
        return
    print("\n[VERBOSE] API Request:")
    print(f"  Method: {method}")
    print(f"  URL: {url}")
    if headers:
        print(f"  Headers: {json.dumps(headers, indent=2)}")
    if body:
        print(f"  Body: {json.dumps(body, indent=2)}")
    if response is not None:
        print(f"  Response Status: {response.status_code}")
        try:
            print(f"  Response Body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"  Response Body (text): {response.text[:500]}")
    print("")


def does_ngrok_exist():
    """Create the directory if needed and check whether ngrok exists."""
    ngpath.mkdir(parents=True, exist_ok=True)

    ngrok_path = ngpath / ngrok_executable

    if ngrok_path.is_file():
        vprint(f"[VERBOSE] Ngrok found at: {ngrok_path}")
        print(f"[+] Ngrok already exists: {ngrok_path}")
        return True

    vprint("[VERBOSE] Ngrok not found.")
    print("[!] Ngrok not found.")
    return False


def DownloadNgrok(url, path):
    try:
        vprint(f"[VERBOSE] Downloading ngrok from: {url}")
        vprint(f"[VERBOSE] Destination directory: {path}")
        print("[+] Downloading ngrok...")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = io.BytesIO()

        with tqdm(
            total=total_size,
            desc="Downloading",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as progress:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded.write(chunk)
                    progress.update(len(chunk))

        print("[+] Extracting ngrok...")
        vprint(f"[VERBOSE] Extracting to: {path}")

        downloaded.seek(0)

        with zipfile.ZipFile(downloaded) as zip_ref:
            zip_ref.extractall(path)

        # Make executable on Linux/macOS
        ngrok_path = Path(path) / ngrok_executable
        if ngrok_path.exists():
            try:
                subprocess.run('chmod +x ' + str(ngrok_path), shell=True, check=True)
                ngrok_path.chmod(0o755)
                vprint(f"[VERBOSE] Made executable: {ngrok_path}")
            except Exception as e:
                vprint(f"[VERBOSE] Could not make executable: {e}")

        print("[+] Ngrok downloaded and extracted successfully.")

    except requests.RequestException as e:
        print(f"[!] Download failed: {e}")
        if config.get("verbose"):
            import traceback
            traceback.print_exc()
    except zipfile.BadZipFile:
        print("[!] Downloaded file is not a valid ZIP archive.")
    except Exception as e:
        print(f"[!] An error occurred: {e}")
        if config.get("verbose"):
            import traceback
            traceback.print_exc()


def check_if_service_id_exists():
    """Check if the service ID exists in the config."""
    if not config.get("service-token") or not config.get("service-id"):
        vprint("[VERBOSE] Missing service-token or service-id, cannot check existence.")
        return False, None

    headers = {
        "Authorization": f"Bearer {config['service-token']}",
        "Service-Link-Id": config['service-id'],
    }
    url = f"{config['linkfroge_api']}/get_link"
    vprint_request("GET", url, headers=headers)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            vprint("[VERBOSE] Service ID exists.")
            print("[+] Service ID exists.")
            return True, response.json().get('link')
        else:
            vprint(f"[VERBOSE] Service ID check failed with status {response.status_code}")
            print("[!] Service ID does not exist.")
            return False, None
    except Exception as e:
        vprint(f"[VERBOSE] Exception checking service ID: {e}")
        print("[!] Failed to check service ID.")
        return False, None


def update_service_link(new_link):
    """Update the service link in the config."""
    headers = {
        "Authorization": f"Bearer {config['service-token']}",
    }
    body = {
        "Service-Link-Id": config['service-id'],
        "link": new_link,
    }
    url = f"{config['linkfroge_api']}/update_link"
    vprint_request("POST", url, headers=headers, body=body)
    try:
        response = requests.post(url, headers=headers, json=body)
        vprint_request("POST", url, headers=headers, body=body, response=response)
        if response.status_code == 200:
            print("[+] Service link updated successfully.")
            return True
        else:
            print(f"[!] Failed to update service link. Status: {response.status_code}")
            return False
    except Exception as e:
        vprint(f"[VERBOSE] Exception updating service link: {e}")
        print("[!] Failed to update service link.")
        return False


def is_ng_auth_token_valid():
    """Check if the ngrok auth token is valid."""
    vprint("[VERBOSE] Checking ngrok auth token...")
    auth_file = ngpath / "ngrok.yml"
    if auth_file.exists():
        vprint(f"[VERBOSE] Auth file found: {auth_file}")
        print("[+] Ngrok auth token is valid.")
        return True
    else:
        vprint("[VERBOSE] No ngrok.yml found, prompting for auth token.")
        print("[!] Ngrok auth token not found.")
        prompt_auth_token = input("[+] Please enter your ngrok auth token: ")
        try:
            vprint(f"[VERBOSE] Running: {ngpath / ngrok_executable} add-authtoken ...")
            subprocess.run(
                [
                    str(ngpath / ngrok_executable),
                    "add-authtoken", prompt_auth_token,
                    "--config", str(ngpath / "ngrok.yml")
                ],
                check=True
            )
            vprint("[VERBOSE] Auth token added successfully.")
            return True
        except Exception as e:
            vprint(f"[VERBOSE] Failed to add auth token: {e}")
            print(f"[!] Failed to add ngrok auth token: {e}")
            return False


def start_ngrok(port):
    """Start ngrok on the specified port."""
    try:
        cmd = [
            str(ngpath / ngrok_executable),
            "http", str(port),
            "--config", str(ngpath / "ngrok.yml")
        ]
        vprint(f"[VERBOSE] Starting ngrok with command: {' '.join(cmd)}")
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[+] Ngrok started on port {port}.")
    except Exception as e:
        vprint(f"[VERBOSE] Failed to start ngrok: {e}")
        print(f"[!] Failed to start ngrok: {e}")


def stop_ngrok():
    """Stop ngrok by terminating the process."""
    try:
        if platform.system() == "Windows":
            vprint("[VERBOSE] Stopping ngrok with taskkill.")
            subprocess.run(["taskkill", "/F", "/IM", ngrok_executable], check=True)
        else:
            vprint("[VERBOSE] Stopping ngrok with pkill.")
            subprocess.run(["pkill", "-f", ngrok_executable], check=True)
        print("[+] Ngrok stopped.")
    except Exception as e:
        vprint(f"[VERBOSE] Failed to stop ngrok: {e}")
        print(f"[!] Failed to stop ngrok: {e}")


def get_ngrok_link():
    """Get the public link from the local ngrok API."""
    vprint(f"[VERBOSE] Querying local ngrok API: {config['localng-api']}")
    try:
        response = requests.get(config['localng-api'], timeout=3)
        vprint_request("GET", config['localng-api'], response=response)
        if response.status_code == 200:
            tunnels = response.json().get("tunnels", [])
            if tunnels:
                public_url = tunnels[0].get("public_url")
                vprint(f"[VERBOSE] Found tunnel: {public_url}")
                print(f"[+] Ngrok public URL: {public_url}")
                return True, public_url
            else:
                vprint("[VERBOSE] No tunnels found.")
                print("[!] No tunnels found.")
                return False, None
        else:
            vprint(f"[VERBOSE] Local ngrok API returned status {response.status_code}")
            print("[!] Failed to get ngrok tunnels.")
            return False, None
    except requests.RequestException as e:
        vprint(f"[VERBOSE] Error connecting to local ngrok API: {e}")
        print(f"[!] Error connecting to local ngrok API: {e}")
        return False, None


def main():
    """Main function to handle the linkFroge process."""
    parser = argparse.ArgumentParser(description="LinkFroge - Create a link for your local server using ngrok.")
    parser.add_argument("--port", type=int, default=55555, help="Port to expose via ngrok")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output – shows every step, request, and retry.")
    parser.add_argument("--service-id", type=str, help="Service ID for LinkFroge")
    parser.add_argument("--service-token", type=str, help="Service token for LinkFroge")
    parser.add_argument("--download-ngrok", type=str, default=config["download-ngrok"], help="URL to download ngrok if not present")
    parser.add_argument("--ngrok-auth-token", type=str, help="Ngrok auth token to authenticate with ngrok")
    parser.add_argument("--linkfroge-api", type=str, default=config["linkfroge_api"], help="LinkFroge API endpoint")
    parser.add_argument("--register-service-id", action="store_true", help="Register a new service ID with LinkFroge")

    args = parser.parse_args()

    # Update config
    config["port"] = args.port
    config["verbose"] = args.verbose
    if args.service_id:
        config["service-id"] = args.service_id
    if args.service_token:
        config["service-token"] = args.service_token
    if args.download_ngrok:
        config["download-ngrok"] = args.download_ngrok
    if args.ngrok_auth_token:
        config["ng-auth-token"] = args.ngrok_auth_token
    if args.linkfroge_api:
        config["linkfroge_api"] = args.linkfroge_api
    if args.register_service_id:
        config["Register-service-id"] = True

    # If verbose, print the full configuration
    if config["verbose"]:
        print("\n[VERBOSE] Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print(f"  args: {vars(args)}")
        print("")

    # If the LinkFroge API is on localhost with HTTPS, switch to HTTP
    url = config["linkfroge_api"]
    if url.startswith("https://127.0.0.1") or url.startswith("https://localhost"):
        config["linkfroge_api"] = url.replace("https://", "http://")
        if config["verbose"]:
            print("[*] Changed LinkFroge API to HTTP for localhost.")

    # Store info for later use
    onStartInfo["service_id"] = config["service-id"]
    onStartInfo["service_token"] = config["service-token"]
    onStartInfo["args"] = vars(args)

    # 1. Ensure ngrok is present
    vprint("[VERBOSE] Step 1: Checking for ngrok...")
    if not does_ngrok_exist():
        DownloadNgrok(config["download-ngrok"], config["ngpath"])

    # 2. Ensure ngrok auth token is set
    vprint("[VERBOSE] Step 2: Validating ngrok auth token...")
    if not is_ng_auth_token_valid():
        print("[!] Ngrok authentication failed. Exiting.")
        return

    # 3. Start ngrok on the specified port
    vprint(f"[VERBOSE] Step 3: Starting ngrok on port {config['port']}...")
    print(f"[+] Starting ngrok on port {config['port']}...")
    start_ngrok(config["port"])

    # 4. Wait for ngrok to be ready and retrieve the public URL
    public_url = None
    max_retries = 12
    retry_delay = 1.5

    vprint(f"[VERBOSE] Step 4: Waiting for ngrok tunnel (max {max_retries} retries, delay {retry_delay}s)...")
    for attempt in range(max_retries):
        time.sleep(retry_delay)
        success, url = get_ngrok_link()
        if success and url:
            public_url = url
            break
        if config["verbose"]:
            print(f"[*] Attempt {attempt + 1}/{max_retries} - ngrok not ready yet, retrying...")

    if not public_url:
        print("[!] Failed to obtain ngrok public URL after multiple attempts.")
        stop_ngrok()
        return

    # 5. Update or display LinkFroge service link
    service_id = config.get("service-id")
    service_token = config.get("service-token")
    vprint("[VERBOSE] Step 5: Handling LinkFroge service link...")

    if service_id and service_token:
        exists, current_link = check_if_service_id_exists()
        if exists:
            if current_link != public_url:
                vprint(f"[VERBOSE] Current link ({current_link}) differs from new link ({public_url}). Updating...")
                headers = {
                    "Authorization": f"Bearer {service_token}",
                    "Service-Link-Id": service_id,
                }
                body = {"link": public_url}
                try:
                    response = requests.post(
                        f"{config['linkfroge_api']}/update_link",
                        headers=headers,
                        json=body
                    )
                    vprint_request("POST", f"{config['linkfroge_api']}/update_link", headers=headers, body=body, response=response)
                    if response.status_code == 200:
                        print(f"[+] Service link updated to: {public_url}")
                    else:
                        print(f"[!] Failed to update service link. Status: {response.status_code}, Response: {response.text}")
                except Exception as e:
                    vprint(f"[VERBOSE] Exception updating service link: {e}")
                    print(f"[!] Error updating service link: {e}")
            else:
                print(f"[!] No need to update. the link is not changed. Current link: {current_link}, New link: {public_url}")
        else:
            print("[!] Service ID does not exist. Please create the service first via the LinkFroge API.")
            print(f"    Then update the link manually with: {public_url}")
    else:
        # No credentials – just print the link
        print("[+] Ngrok tunnel is running. Public URL:", public_url)
        print("[!] To link this tunnel with a LinkFroge service, provide --service-id and --service-token.")

    # Store the link for later reference
    onStartInfo["service_link"] = public_url

    # 6. Register the service ID if requested
    if config.get("Register-service-id") and config.get("service-token"):
        vprint("[VERBOSE] Step 6: Registering service ID with LinkFroge...")
        print("[+] Registering service ID with LinkFroge...")
        headers = {
            "Authorization": f"Bearer {config['service-token']}",
        }
        body = {
            "link": public_url,
        }
        url = f"{config['linkfroge_api']}/register_service"
        vprint_request("POST", url, headers=headers, body=body)
        try:
            response = requests.post(url, headers=headers, json=body)
            vprint_request("POST", url, headers=headers, body=body, response=response)
            if response.status_code == 200:
                print("[+] Service ID registered successfully.")
                response_data = response.json()
                service_link_id = response_data.get("service_link_id")
                onStartInfo["service_id"] = service_link_id
                if service_link_id:
                    print(f"[+] Service Link ID: {service_link_id}")
                    config["service-id"] = service_link_id
            else:
                print(f"[!] Failed to register service ID. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            vprint(f"[VERBOSE] Exception registering service ID: {e}")
            print(f"[!] Error registering service ID: {e}")

    # 7. Keep the script alive until interrupted
    vprint("[VERBOSE] Step 7: Running tunnel indefinitely (press Ctrl+C to stop).")
    print("\n[+] Ngrok tunnel is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Stopping ngrok...")
        stop_ngrok()
        print("[+] Done.")

if __name__ == "__main__":
    main()