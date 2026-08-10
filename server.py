
from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import requests
import threading
import subprocess
import time


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

DOWNLOAD_FOLDER = "/app/downloads"

BGUTIL_URL = "http://127.0.0.1:4416"

BGUTIL_SERVER_DIRECTORY = (
    "/app/bgutil-ytdlp-pot-provider/server"
)

NODE_PATH = "/usr/bin/node"


os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# BGUTIL PROCESS
# ============================================================

bgutil_process = None


def start_bgutil():

    global bgutil_process

    print()
    print("================================")
    print("STARTING BGUTIL PO TOKEN SERVER")
    print("================================")

    if not os.path.isdir(
        BGUTIL_SERVER_DIRECTORY
    ):

        print(
            "BGUTIL SERVER DIRECTORY NOT FOUND:",
            BGUTIL_SERVER_DIRECTORY
        )

        return False

    package_json = os.path.join(
        BGUTIL_SERVER_DIRECTORY,
        "package.json"
    )

    if not os.path.isfile(package_json):

        print(
            "BGUTIL package.json NOT FOUND:",
            package_json
        )

        return False

    print(
        "BGUTIL DIRECTORY:",
        BGUTIL_SERVER_DIRECTORY
    )

    try:

        print(
            "Starting bgutil HTTP server..."
        )

        bgutil_process = subprocess.Popen(
            [
                "npm",
                "start"
            ],

            cwd=BGUTIL_SERVER_DIRECTORY,

            stdout=subprocess.PIPE,

            stderr=subprocess.STDOUT,

            text=True,

            bufsize=1
        )

        print(
            "BGUTIL PROCESS STARTED"
        )

        print(
            "BGUTIL PID:",
            bgutil_process.pid
        )

        def read_bgutil_output():

            if not bgutil_process.stdout:
                return

            for line in bgutil_process.stdout:

                print(
                    "[BGUTIL]",
                    line.rstrip()
                )

        output_thread = threading.Thread(
            target=read_bgutil_output,
            daemon=True
        )

        output_thread.start()

        return True

    except Exception as e:

        print(
            "BGUTIL START ERROR:",
            str(e)
        )

        return False


# ============================================================
# CHECK BGUTIL
# ============================================================

def check_bgutil():

    try:

        ping_url = (
            BGUTIL_URL +
            "/ping"
        )

        response = requests.get(
            ping_url,
            timeout=5
        )

        print(
            "BGUTIL PING URL:",
            ping_url
        )

        print(
            "BGUTIL HTTP STATUS:",
            response.status_code
        )

        if response.status_code == 200:

            print(
                "BGUTIL HTTP SERVER: READY"
            )

            return True

        print(
            "BGUTIL HTTP SERVER: REACHABLE "
            "BUT /ping RETURNED:",
            response.status_code
        )

        print(
            "BGUTIL RESPONSE:",
            response.text
        )

        return False

    except Exception as e:

        print(
            "BGUTIL HTTP SERVER: NOT REACHABLE"
        )

        print(
            "BGUTIL ERROR:",
            str(e)
        )

        return False


# ============================================================
# WAIT FOR BGUTIL
# ============================================================

def initialize_bgutil():

    started = start_bgutil()

    if not started:

        print(
            "BGUTIL FAILED TO START"
        )

        return

    print(
        "WAITING FOR BGUTIL..."
    )

    # Give npm/node time to start.
    for attempt in range(15):

        time.sleep(1)

        print(
            "BGUTIL CHECK",
            attempt + 1,
            "/ 15"
        )

        if check_bgutil():

            print(
                "================================"
            )

            print(
                "BGUTIL IS READY"
            )

            print(
                "================================"
            )

            return

    print(
        "================================"
    )

    print(
        "BGUTIL DID NOT BECOME READY"
    )

    print(
        "================================"
    )


# ============================================================
# START BGUTIL IN BACKGROUND
# ============================================================

bgutil_thread = threading.Thread(
    target=initialize_bgutil,
    daemon=True
)

bgutil_thread.start()


# ============================================================
# YT-DLP OPTIONS
# ============================================================

def create_yt_dlp_options(
    skip_download=True
):

    options = {

        # ----------------------------------------------------
        # General
        # ----------------------------------------------------

        "quiet": False,

        "no_warnings": False,

        "verbose": True,

        "skip_download": skip_download,

        "noplaylist": True,

        # ----------------------------------------------------
        # Node.js
        # ----------------------------------------------------

        "js_runtimes": {

            "node": {

                "path": NODE_PATH

            }

        },

        # ----------------------------------------------------
        # BGUTIL PO TOKEN PROVIDER
        # ----------------------------------------------------

        "extractor_args": {

            "youtubepot-bgutilhttp": {

                "base_url": BGUTIL_URL

            },

            # YouTube client configuration.
            #
            # mweb is important for the current
            # PO-token flow.
            #

            "youtube": {

                "player_client": [

                    "mweb",

                    "default"

                ]

            }

        },

        # ----------------------------------------------------
        # HTTP HEADERS
        # ----------------------------------------------------

        "http_headers": {

            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/144.0.0.0 "
                "Safari/537.36"
            ),

            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),

            "Accept-Language": (
                "en-US,en;q=0.9"
            ),

            "Sec-Fetch-Mode": (
                "navigate"
            )

        },

        # ----------------------------------------------------
        # RETRIES
        # ----------------------------------------------------

        "retries": 3,

        "fragment_retries": 3

    }

    return options


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify({

        "success": True,

        "message":
            "YT Downloader server is running",

        "server":
            "running",

        "yt_dlp_version":
            yt_dlp.version.__version__,

        "bgutil_url":
            BGUTIL_URL

    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    bgutil_ok = check_bgutil()

    return jsonify({

        "success": True,

        "server":
            "running",

        "bgutil":
            bgutil_ok,

        "yt_dlp_version":
            yt_dlp.version.__version__

    })


# ============================================================
# GET VIDEO INFORMATION
# ============================================================

@app.route(
    "/info",
    methods=["POST"]
)
def get_info():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "error":
                    "Invalid JSON request"

            }), 400

        url = data.get(
            "url",
            ""
        ).strip()

        if not url:

            return jsonify({

                "success": False,

                "error":
                    "URL is required"

            }), 400

        print()
        print("================================")
        print("INFO REQUEST")
        print("URL:", url)
        print("================================")

        print(
            "YT-DLP VERSION:",
            yt_dlp.version.__version__
        )

        print(
            "Node.js path:",
            NODE_PATH
        )

        print(
            "Node.js exists:",
            os.path.exists(NODE_PATH)
        )

        print(
            "BGUTIL URL:",
            BGUTIL_URL
        )

        bgutil_ready = check_bgutil()

        print(
            "BGUTIL READY:",
            bgutil_ready
        )

        if not bgutil_ready:

            print(
                "WARNING: BGUTIL IS NOT READY"
            )

        # ----------------------------------------------------
        # Create yt-dlp options
        # ----------------------------------------------------

        options = create_yt_dlp_options(
            skip_download=True
        )

        print(
            "YT-DLP OPTIONS CREATED"
        )

        print(
            "STARTING YT-DLP EXTRACTION NOW"
        )

        # ----------------------------------------------------
        # Extract
        # ----------------------------------------------------

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        # ----------------------------------------------------
        # Basic information
        # ----------------------------------------------------

        title = info.get(
            "title",
            "Unknown title"
        )

        thumbnail = info.get(
            "thumbnail",
            ""
        )

        duration_seconds = info.get(
            "duration",
            0
        )

        if duration_seconds:

            minutes = int(
                duration_seconds // 60
            )

            seconds = int(
                duration_seconds % 60
            )

            duration = (
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        else:

            duration = "Unknown"

        # ----------------------------------------------------
        # Formats
        # ----------------------------------------------------

        formats = info.get(
            "formats",
            []
        )

        qualities = []

        for fmt in formats:

            format_id = fmt.get(
                "format_id"
            )

            height = fmt.get(
                "height"
            )

            extension = fmt.get(
                "ext"
            )

            if not format_id:
                continue

            if not height:
                continue

            try:

                height = int(
                    height
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            # Only expose actual video formats.
            #
            # This prevents thumbnail/storyboard formats
            # such as sb1, sb2, sb3 from being returned.

            vcodec = fmt.get(
                "vcodec"
            )

            if not vcodec:
                continue

            qualities.append({

                "format_id":
                    str(format_id),

                "height":
                    height,

                "ext":
                    extension or ""

            })

        # ----------------------------------------------------
        # Remove duplicate resolutions
        # ----------------------------------------------------

        unique_qualities = {}

        for quality in qualities:

            height = quality["height"]

            if height not in unique_qualities:

                unique_qualities[
                    height
                ] = quality

        qualities = list(
            unique_qualities.values()
        )

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        qualities.sort(
            key=lambda x: x["height"]
        )

        print(
            "TITLE:",
            title
        )

        print(
            "DURATION:",
            duration
        )

        print(
            "FOUND",
            len(qualities),
            "VIDEO QUALITIES"
        )

        print(
            "================================"
        )

        return jsonify({

            "success": True,

            "title":
                title,

            "thumbnail":
                thumbnail,

            "duration":
                duration,

            "qualities":
                qualities

        })

    except Exception as e:

        print()
        print("================================")
        print("INFO ERROR")
        print(str(e))
        print("================================")
        print()

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# DOWNLOAD VIDEO
# ============================================================

@app.route(
    "/download",
    methods=["POST"]
)
def download():

    file_id = None

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "error":
                    "Invalid JSON request"

            }), 400

        url = data.get(
            "url",
            ""
        ).strip()

        format_id = str(
            data.get(
                "format_id",
                ""
            )
        ).strip()

        if not url:

            return jsonify({

                "success": False,

                "error":
                    "URL is required"

            }), 400

        if not format_id:

            return jsonify({

                "success": False,

                "error":
                    "Format is required"

            }), 400

        # ----------------------------------------------------
        # File ID
        # ----------------------------------------------------

        file_id = str(
            uuid.uuid4()
        )

        output_template = os.path.join(

            DOWNLOAD_FOLDER,

            file_id +
            ".%(ext)s"

        )

        print()
        print("================================")
        print("STARTING DOWNLOAD")
        print("================================")
        print("URL:", url)
        print("FORMAT:", format_id)
        print("FILE ID:", file_id)
        print("================================")
        print()

        # ----------------------------------------------------
        # BGUTIL
        # ----------------------------------------------------

        print(
            "BGUTIL STATUS BEFORE DOWNLOAD:"
        )

        bgutil_ready = check_bgutil()

        if not bgutil_ready:

            print(
                "WARNING: BGUTIL IS NOT READY"
            )

        # ----------------------------------------------------
        # yt-dlp options
        # ----------------------------------------------------

        ydl_opts = create_yt_dlp_options(
            skip_download=False
        )

        # ----------------------------------------------------
        # Format
        # ----------------------------------------------------
        #
        # First try the selected video format + audio.
        #
        # If that exact combination isn't available,
        # fall back to best video + best audio.
        #

        ydl_opts.update({

            "format": (
                f"{format_id}+bestaudio/"
                f"{format_id}/"
                f"bestvideo+bestaudio/"
                f"best"
            ),

            "outtmpl":
                output_template,

            "merge_output_format":
                "mp4"

        })

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        print(
            "STARTING YT-DLP DOWNLOAD"
        )

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            ydl.extract_info(
                url,
                download=True
            )

        # ----------------------------------------------------
        # Find downloaded file
        # ----------------------------------------------------

        downloaded_file = None

        for filename in os.listdir(
            DOWNLOAD_FOLDER
        ):

            if not filename.startswith(
                file_id
            ):

                continue

            filepath = os.path.join(
                DOWNLOAD_FOLDER,
                filename
            )

            if os.path.isfile(
                filepath
            ):

                downloaded_file = filepath

                break

        # ----------------------------------------------------
        # File not found
        # ----------------------------------------------------

        if not downloaded_file:

            return jsonify({

                "success": False,

                "error":
                    "Download completed but file was not found"

            }), 500

        # ----------------------------------------------------
        # Filename
        # ----------------------------------------------------

        filename = os.path.basename(
            downloaded_file
        )

        print()
        print("================================")
        print("DOWNLOAD COMPLETE")
        print("================================")
        print("FILE:", filename)
        print("================================")
        print()

        return jsonify({

            "success": True,

            "file_id":
                file_id,

            "filename":
                filename

        })

    except Exception as e:

        print()
        print("================================")
        print("DOWNLOAD ERROR")
        print("================================")
        print(str(e))
        print("================================")
        print()

        # ----------------------------------------------------
        # Cleanup partial files
        # ----------------------------------------------------

        if file_id:

            try:

                for filename in os.listdir(
                    DOWNLOAD_FOLDER
                ):

                    if not filename.startswith(
                        file_id
                    ):

                        continue

                    filepath = os.path.join(
                        DOWNLOAD_FOLDER,
                        filename
                    )

                    if not os.path.isfile(
                        filepath
                    ):

                        continue

                    try:

                        os.remove(
                            filepath
                        )

                        print(
                            "Deleted partial file:",
                            filepath
                        )

                    except Exception as cleanup_error:

                        print(
                            "Could not delete:",
                            filepath
                        )

                        print(
                            cleanup_error
                        )

            except Exception as cleanup_error:

                print(
                    "Partial-file cleanup error:",
                    cleanup_error
                )

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# SEND FILE TO ANDROID
# ============================================================

@app.route(
    "/file/<file_id>",
    methods=["GET"]
)
def get_file(file_id):

    try:

        filepath = None

        for filename in os.listdir(
            DOWNLOAD_FOLDER
        ):

            if not filename.startswith(
                file_id
            ):

                continue

            possible_path = os.path.join(
                DOWNLOAD_FOLDER,
                filename
            )

            if os.path.isfile(
                possible_path
            ):

                filepath = possible_path

                break

        if not filepath:

            return jsonify({

                "success": False,

                "error":
                    "File not found"

            }), 404

        print()
        print("================================")
        print("SENDING FILE")
        print("================================")
        print(filepath)
        print("================================")
        print()

        return send_file(

            filepath,

            as_attachment=True,

            download_name=os.path.basename(
                filepath
            ),

            mimetype="video/mp4"

        )

    except Exception as e:

        print()
        print("================================")
        print("FILE ERROR")
        print("================================")
        print(str(e))
        print("================================")
        print()

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# CLEANUP TEMPORARY FILE
# ============================================================

@app.route(
    "/cleanup/<file_id>",
    methods=["DELETE"]
)
def cleanup_file(file_id):

    try:

        filepath = None

        for filename in os.listdir(
            DOWNLOAD_FOLDER
        ):

            if not filename.startswith(
                file_id
            ):

                continue

            possible_path = os.path.join(
                DOWNLOAD_FOLDER,
                filename
            )

            if os.path.isfile(
                possible_path
            ):

                filepath = possible_path

                break

        # ----------------------------------------------------
        # Already deleted
        # ----------------------------------------------------

        if not filepath:

            return jsonify({

                "success": True,

                "message":
                    "File already deleted"

            })

        # ----------------------------------------------------
        # Delete
        # ----------------------------------------------------

        try:

            os.remove(
                filepath
            )

        except PermissionError:

            return jsonify({

                "success": False,

                "error":
                    "File is still being used"

            }), 409

        print()
        print("================================")
        print("TEMPORARY FILE DELETED")
        print("================================")
        print(filepath)
        print("================================")
        print()

        return jsonify({

            "success": True,

            "message":
                "File deleted successfully"

        })

    except Exception as e:

        print()
        print("================================")
        print("CLEANUP ERROR")
        print("================================")
        print(str(e))
        print("================================")
        print()

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print()
    print("================================")
    print("YT DOWNLOADER BACKEND")
    print("================================")

    print(
        "SERVER PORT:",
        port
    )

    print(
        "DOWNLOAD FOLDER:",
        os.path.abspath(
            DOWNLOAD_FOLDER
        )
    )

    print(
        "BGUTIL URL:",
        BGUTIL_URL
    )

    print(
        "NODE PATH:",
        NODE_PATH
    )

    print("================================")
    print()

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )

