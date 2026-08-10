from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import requests
import threading
import subprocess
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
BGUTIL_URL = "http://127.0.0.1:4416"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ============================================================
# BGUTIL PO TOKEN SERVER
# ============================================================

bgutil_process = None


def start_bgutil():
    global bgutil_process

    server_directory = "/app/bgutil-ytdlp-pot-provider/server"

    if not os.path.isdir(server_directory):
        print("BGUTIL SERVER DIRECTORY NOT FOUND")
        return

    print("================================")
    print("STARTING BGUTIL PO TOKEN SERVER")
    print("================================")
    print("Directory:", server_directory)

    try:
        package_json = os.path.join(
            server_directory,
            "package.json"
        )

        if not os.path.isfile(package_json):
            print("BGUTIL package.json NOT FOUND")
            return

        print("Starting bgutil HTTP server...")

        bgutil_process = subprocess.Popen(
            ["npm", "start"],
            cwd=server_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        def read_output():
            if bgutil_process.stdout:
                for line in bgutil_process.stdout:
                    print("[BGUTIL]", line.rstrip())

        output_thread = threading.Thread(
            target=read_output,
            daemon=True
        )

        output_thread.start()

        print("BGUTIL PROCESS STARTED")
        print("PID:", bgutil_process.pid)

    except Exception as e:
        print("BGUTIL START ERROR:", str(e))


def check_bgutil():
    try:
        response = requests.get(
            BGUTIL_URL,
            timeout=5
        )

        print("BGUTIL HTTP STATUS:", response.status_code)
        print("BGUTIL HTTP SERVER: REACHABLE")

        return True

    except Exception as e:
        print("BGUTIL HTTP SERVER: NOT REACHABLE")
        print("BGUTIL ERROR:", str(e))

        return False


def initialize_bgutil():
    start_bgutil()

    time.sleep(3)

    check_bgutil()


# Start bgutil when the application starts.
bgutil_thread = threading.Thread(
    target=initialize_bgutil,
    daemon=True
)

bgutil_thread.start()


# ============================================================
# YT-DLP OPTIONS
# ============================================================

def create_yt_dlp_options(skip_download=True):

    options = {
        "quiet": False,
        "no_warnings": False,
        "verbose": True,
        "skip_download": skip_download,

        "js_runtimes": {
            "node": {
                "path": "/usr/bin/node"
            }
        },

        "extractor_args": {
            "youtubepot-bgutilhttp": {
                "base_url": BGUTIL_URL
            }
        },

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/144.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate"
        }
    }

    return options


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "YT Downloader server is running",
        "yt_dlp_version": yt_dlp.version.__version__,
        "bgutil_url": BGUTIL_URL
    })


@app.route("/health", methods=["GET"])
def health():

    bgutil_ok = check_bgutil()

    return jsonify({
        "success": True,
        "server": "running",
        "bgutil": bgutil_ok,
        "yt_dlp_version": yt_dlp.version.__version__
    })


# ============================================================
# GET VIDEO INFORMATION
# ============================================================

@app.route("/info", methods=["POST"])
def get_info():

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "error": "Invalid JSON request"
            }), 400

        url = data.get(
            "url",
            ""
        ).strip()

        if not url:

            return jsonify({
                "success": False,
                "error": "URL is required"
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
            "/usr/bin/node"
        )

        print(
            "Node.js exists:",
            os.path.exists("/usr/bin/node")
        )

        print(
            "BGUTIL URL:",
            BGUTIL_URL
        )

        check_bgutil()

        options = create_yt_dlp_options(
            skip_download=True
        )

        print("YT-DLP OPTIONS CREATED")
        print("STARTING YT-DLP EXTRACTION NOW")

        with yt_dlp.YoutubeDL(options) as ydl:

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
                f"{minutes:02d}:{seconds:02d}"
            )

        else:

            duration = "Unknown"

        # ----------------------------------------------------
        # Available formats
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
                height = int(height)
            except (TypeError, ValueError):
                continue

            qualities.append({

                "format_id": str(
                    format_id
                ),

                "height": height,

                "ext": extension or ""

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
        # Sort qualities
        # ----------------------------------------------------

        qualities.sort(
            key=lambda x: x["height"]
        )

        print(
            "Found",
            len(qualities),
            "qualities"
        )

        return jsonify({

            "success": True,

            "title": title,

            "thumbnail": thumbnail,

            "duration": duration,

            "qualities": qualities

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

            "error": str(e)

        }), 500


# ============================================================
# DOWNLOAD VIDEO
# ============================================================

@app.route("/download", methods=["POST"])
def download():

    file_id = None

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "error": "Invalid JSON request"

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

                "error": "URL is required"

            }), 400

        if not format_id:

            return jsonify({

                "success": False,

                "error": "Format is required"

            }), 400

        # ----------------------------------------------------
        # File ID
        # ----------------------------------------------------

        file_id = str(
            uuid.uuid4()
        )

        output_template = os.path.join(
            DOWNLOAD_FOLDER,
            file_id + ".%(ext)s"
        )

        print()
        print("================================")
        print("STARTING DOWNLOAD")
        print("================================")
        print("URL:", url)
        print("Format:", format_id)
        print("File ID:", file_id)
        print("================================")
        print()

        print(
            "BGUTIL STATUS BEFORE DOWNLOAD:"
        )

        check_bgutil()

        # ----------------------------------------------------
        # yt-dlp options
        # ----------------------------------------------------

        ydl_opts = create_yt_dlp_options(
            skip_download=False
        )

        ydl_opts.update({

            "format": (
                f"{format_id}+bestaudio/"
                f"{format_id}"
            ),

            "outtmpl":
                output_template,

            "merge_output_format":
                "mp4"

        })

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        print("STARTING YT-DLP DOWNLOAD")

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

            if filename.startswith(
                file_id
            ):

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
        print("File:", filename)
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
        # Delete partial files
        # ----------------------------------------------------

        if file_id:

            try:

                for filename in os.listdir(
                    DOWNLOAD_FOLDER
                ):

                    if filename.startswith(
                        file_id
                    ):

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

            if filename.startswith(
                file_id
            ):

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

            download_name=
                os.path.basename(
                    filepath
                ),

            mimetype=
                "video/mp4"

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

            if filename.startswith(
                file_id
            ):

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
    print("Server running on port:", port)
    print("Download folder:")
    print(
        os.path.abspath(
            DOWNLOAD_FOLDER
        )
    )
    print("BGUTIL URL:")
    print(BGUTIL_URL)
    print("================================")
    print()

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
