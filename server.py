from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import requests
import threading
import subprocess
import time
import base64

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

COOKIE_FILE = "/app/secrets/youtube-cookies.txt"

os.makedirs(
DOWNLOAD_FOLDER,
exist_ok=True
)

os.makedirs(
"/app/secrets",
exist_ok=True
)

# ============================================================

# COOKIE SETUP

# ============================================================

def setup_cookies():
"""
Creates the YouTube cookie file from the optional
YOUTUBE_COOKIES_B64 environment variable.


The cookie file is NEVER stored in the repository.
"""

cookies_b64 = os.environ.get(
    "YOUTUBE_COOKIES_B64",
    ""
).strip()

if not cookies_b64:
    print("YOUTUBE_COOKIES_B64 is not configured")
    return False

try:
    cookie_data = base64.b64decode(
        cookies_b64
    )

    with open(
        COOKIE_FILE,
        "wb"
    ) as f:

        f.write(cookie_data)

    print(
        "YouTube cookie file created:"
    )

    print(
        COOKIE_FILE
    )

    return True

except Exception as e:

    print(
        "FAILED TO CREATE COOKIE FILE:"
    )

    print(
        str(e)
    )

    return False


# ============================================================

# COOKIE STATUS

# ============================================================

def cookies_available():


return (
    os.path.isfile(
        COOKIE_FILE
    )
    and
    os.path.getsize(
        COOKIE_FILE
    ) > 0
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
        "BGUTIL DIRECTORY NOT FOUND:",
        BGUTIL_SERVER_DIRECTORY
    )

    return False

build_file = os.path.join(
    BGUTIL_SERVER_DIRECTORY,
    "build",
    "main.js"
)

if not os.path.isfile(
    build_file
):

    print(
        "BGUTIL BUILD FILE NOT FOUND:",
        build_file
    )

    return False

try:

    bgutil_process = subprocess.Popen(

        [
            NODE_PATH,
            build_file
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

    threading.Thread(
        target=read_bgutil_output,
        daemon=True
    ).start()

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

    response = requests.get(
        BGUTIL_URL,
        timeout=5
    )

    print(
        "BGUTIL HTTP STATUS:",
        response.status_code
    )

    print(
        "BGUTIL HTTP SERVER: REACHABLE"
    )

    return True

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

# INITIALIZE BGUTIL

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

# START BACKGROUND SERVICES

# ============================================================

setup_cookies()

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
    # GENERAL
    # ----------------------------------------------------

    "quiet": False,

    "no_warnings": False,

    "verbose": True,

    "skip_download":
        skip_download,

    "noplaylist":
        True,

    # ----------------------------------------------------
    # COOKIE AUTHENTICATION
    # ----------------------------------------------------

    "cookiefile":
        COOKIE_FILE
        if cookies_available()
        else None,

    # ----------------------------------------------------
    # NODE.JS
    # ----------------------------------------------------

    "js_runtimes": {

        "node": {

            "path":
                NODE_PATH

        }

    },

    # ----------------------------------------------------
    # BGUTIL
    # ----------------------------------------------------

    "extractor_args": {

        "youtubepot-bgutilhttp": {

            "base_url":
                BGUTIL_URL

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
            "Chrome/151.0.0.0 "
            "Safari/537.36"
        ),

        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),

        "Accept-Language":
            "en-US,en;q=0.9"

    },

    # ----------------------------------------------------
    # RETRIES
    # ----------------------------------------------------

    "retries":
        3,

    "fragment_retries":
        3,

    # ----------------------------------------------------
    # FILESYSTEM
    # ----------------------------------------------------

    "restrictfilenames":
        False

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

    "success":
        True,

    "server":
        "running",

    "yt_dlp_version":
        yt_dlp.version.__version__,

    "bgutil":
        check_bgutil(),

    "cookies_configured":
        cookies_available()

})


# ============================================================

# HEALTH

# ============================================================

@app.route(
"/health",
methods=["GET"]
)
def health():


return jsonify({

    "success":
        True,

    "server":
        "running",

    "bgutil":
        check_bgutil(),

    "cookies":
        cookies_available(),

    "yt_dlp_version":
        yt_dlp.version.__version__

})


# ============================================================

# INFO

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

            "success":
                False,

            "error":
                "Invalid JSON request"

        }), 400

    url = data.get(
        "url",
        ""
    ).strip()

    if not url:

        return jsonify({

            "success":
                False,

            "error":
                "URL is required"

        }), 400

    print()
    print("================================")
    print("INFO REQUEST")
    print("================================")

    print(
        "URL:",
        url
    )

    print(
        "YT-DLP:",
        yt_dlp.version.__version__
    )

    print(
        "BGUTIL:",
        check_bgutil()
    )

    print(
        "COOKIES:",
        cookies_available()
    )

    options = create_yt_dlp_options(
        skip_download=True
    )

    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

    # ----------------------------------------------------
    # BASIC INFO
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
    # VIDEO FORMATS
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

        vcodec = fmt.get(
            "vcodec"
        )

        if not format_id:
            continue

        if not height:
            continue

        if not vcodec:
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

        qualities.append({

            "format_id":
                str(format_id),

            "height":
                height,

            "ext":
                extension or ""

        })

    # ----------------------------------------------------
    # ONE FORMAT PER RESOLUTION
    # ----------------------------------------------------

    unique = {}

    for quality in qualities:

        height = quality[
            "height"
        ]

        if height not in unique:

            unique[
                height
            ] = quality

    qualities = list(
        unique.values()
    )

    qualities.sort(
        key=lambda x:
            x["height"]
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
        "VIDEO QUALITIES:",
        len(qualities)
    )

    return jsonify({

        "success":
            True,

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
    print("================================")
    print(
        str(e)
    )
    print("================================")

    return jsonify({

        "success":
            False,

        "error":
            str(e)

    }), 500


# ============================================================

# DOWNLOAD

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

            "success":
                False,

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

            "success":
                False,

            "error":
                "URL is required"

        }), 400

    if not format_id:

        return jsonify({

            "success":
                False,

            "error":
                "Format is required"

        }), 400

    # ----------------------------------------------------
    # AUTHENTICATION REQUIREMENT
    # ----------------------------------------------------

    if not cookies_available():

        return jsonify({

            "success":
                False,

            "error":
                "Authenticated YouTube cookie file is not configured"

        }), 503

    # ----------------------------------------------------
    # FILE ID
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
    print("STARTING AUTHENTICATED DOWNLOAD")
    print("================================")

    print(
        "URL:",
        url
    )

    print(
        "FORMAT:",
        format_id
    )

    print(
        "FILE ID:",
        file_id
    )

    print(
        "COOKIES:",
        True
    )

    print(
        "BGUTIL:",
        check_bgutil()
    )

    print("================================")

    # ----------------------------------------------------
    # OPTIONS
    # ----------------------------------------------------

    ydl_opts = create_yt_dlp_options(
        skip_download=False
    )

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
    # DOWNLOAD
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
    # FIND FILE
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

    if not downloaded_file:

        return jsonify({

            "success":
                False,

            "error":
                "Download completed but output file was not found"

        }), 500

    filename = os.path.basename(
        downloaded_file
    )

    print()
    print("================================")
    print("DOWNLOAD COMPLETE")
    print("================================")

    print(
        "FILE:",
        filename
    )

    print("================================")

    return jsonify({

        "success":
            True,

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

    print(
        str(e)
    )

    print("================================")

    # ----------------------------------------------------
    # CLEANUP
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

                if os.path.isfile(
                    filepath
                ):

                    try:

                        os.remove(
                            filepath
                        )

                    except Exception:

                        pass

        except Exception:

            pass

    return jsonify({

        "success":
            False,

        "error":
            str(e)

    }), 500


# ============================================================

# SEND FILE

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

            "success":
                False,

            "error":
                "File not found"

        }), 404

    return send_file(

        filepath,

        as_attachment=True,

        download_name=
            os.path.basename(
                filepath
            ),

        mimetype=
            "video/mp4"

    )

except Exception as e:

    return jsonify({

        "success":
            False,

        "error":
            str(e)

    }), 500


# ============================================================

# CLEANUP

# ============================================================

@app.route(
"/cleanup/<file_id>",
methods=["DELETE"]
)
def cleanup_file(file_id):


try:

    deleted = False

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

            deleted = True

        except PermissionError:

            return jsonify({

                "success":
                    False,

                "error":
                    "File is still being used"

            }), 409

    return jsonify({

        "success":
            True,

        "message":
            "File deleted"
            if deleted
            else
            "File already deleted"

    })

except Exception as e:

    return jsonify({

        "success":
            False,

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
        "5000"
    )
)

print()
print("================================")
print("YT DOWNLOADER BACKEND")
print("================================")

print(
    "PORT:",
    port
)

print(
    "YT-DLP:",
    yt_dlp.version.__version__
)

print(
    "BGUTIL:",
    BGUTIL_URL
)

print(
    "COOKIES:",
    cookies_available()
)

print("================================")

app.run(

    host="0.0.0.0",

    port=port,

    debug=False

)

