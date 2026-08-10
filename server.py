
from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import requests

# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

DOWNLOAD_FOLDER = "/app/downloads"

BGUTIL_URL = "http://127.0.0.1:4416"

NODE_PATH = "/usr/bin/node"

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)

# ============================================================
# CHECK BGUTIL
#
# BGUTIL is started by the Dockerfile with:
#
# node build/main.js
#
# DO NOT START BGUTIL FROM PYTHON.
# ============================================================

def check_bgutil():

    try:

        # The BGUTIL server does not necessarily expose
        # /ping, so a 404 still proves that the HTTP server
        # itself is alive and reachable.
        response = requests.get(
            BGUTIL_URL,
            timeout=5
        )

        print(
            "BGUTIL URL:",
            BGUTIL_URL
        )

        print(
            "BGUTIL HTTP STATUS:",
            response.status_code
        )

        # Any HTTP response means the server is reachable.
        # 404 is expected for the root URL.
        if response.status_code in (
            200,
            404,
            405
        ):

            print(
                "BGUTIL HTTP SERVER: REACHABLE"
            )

            return True

        print(
            "BGUTIL HTTP SERVER: REACHABLE "
            "BUT RETURNED:",
            response.status_code
        )

        print(
            "BGUTIL RESPONSE:",
            response.text[:500]
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

        "skip_download":
            skip_download,

        "noplaylist": True,

        # ----------------------------------------------------
        # Node.js
        # ----------------------------------------------------

        "js_runtimes": {

            "node": {

                "path":
                    NODE_PATH

            }

        },

        # ----------------------------------------------------
        # BGUTIL PO TOKEN PROVIDER
        # ----------------------------------------------------

        "extractor_args": {

            "youtubepot-bgutilhttp": {

                "base_url":
                    BGUTIL_URL

            },

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

            "Accept-Language":
                "en-US,en;q=0.9",

            "Sec-Fetch-Mode":
                "navigate"

        },

        # ----------------------------------------------------
        # Retries
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

    bgutil_ok = check_bgutil()

    return jsonify({

        "success": True,

        "message":
            "YT Downloader server is running",

        "server":
            "running",

        "bgutil":
            bgutil_ok,

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
            os.path.exists(
                NODE_PATH
            )
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
        # yt-dlp options
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

            vcodec = fmt.get(
                "vcodec"
            )

            # Ignore invalid formats
            if not format_id:
                continue

            if not height:
                continue

            # Ignore audio-only formats
            if not vcodec:
                continue

            # Ignore storyboard / thumbnail formats
            if str(format_id).startswith(
                "sb"
            ):
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
        # Remove duplicate resolutions
        # ----------------------------------------------------

        unique_qualities = {}

        for quality in qualities:

            height = quality[
                "height"
            ]

            # Prefer MP4 when several formats
            # have the same resolution.

            if height not in unique_qualities:

                unique_qualities[
                    height
                ] = quality

            else:

                current = unique_qualities[
                    height
                ]

                if (
                    quality["ext"] == "mp4"
                    and current["ext"] != "mp4"
                ):

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
        print(str(e))
        print("================================")
        print()

        return jsonify({

            "success":
                False,

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

                "success":
                    False,

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

            "success":
                False,

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

                "success":
                    False,

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

            "success":
                False,

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

                "success":
                    True,

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

                "success":
                    False,

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

            "success":
                True,

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
        DOWNLOAD_FOLDER
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

