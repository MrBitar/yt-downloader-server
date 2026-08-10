from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)

# ============================================================
# BGUTIL PO-TOKEN PROVIDER
# ============================================================

BGUTIL_SERVER_HOME = (
    "/app/bgutil-ytdlp-pot-provider/server"
)


# ============================================================
# COMMON YT-DLP OPTIONS
# ============================================================

def get_ytdlp_options(extra_options=None):

    options = {

        # ----------------------------------------------------
        # Enable Node.js JavaScript runtime
        # ----------------------------------------------------

        "js_runtimes": {
            "node": {
                "path": "/usr/bin/node"
            }
        },

        # ----------------------------------------------------
        # BGUTIL PO-token provider
        # ----------------------------------------------------

        "extractor_args": {

            "youtubepot-bgutilscript": {

                "server_home":
                    BGUTIL_SERVER_HOME

            }

        }

    }

    if extra_options:

        options.update(
            extra_options
        )

    return options


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

        print(
            "",
            flush=True
        )

        print(
            "================================",
            flush=True
        )

        print(
            "INFO REQUEST",
            flush=True
        )

        print(
            "URL:",
            url,
            flush=True
        )

        print(
            "================================",
            flush=True
        )

        # ----------------------------------------------------
        # Diagnostics
        # ----------------------------------------------------

        print(
            "YT-DLP VERSION:",
            yt_dlp.version.__version__,
            flush=True
        )

        print(
            "Node.js path:",
            "/usr/bin/node",
            flush=True
        )

        print(
            "Node.js exists:",
            os.path.exists(
                "/usr/bin/node"
            ),
            flush=True
        )

        print(
            "BGUTIL directory exists:",
            os.path.exists(
                BGUTIL_SERVER_HOME
            ),
            flush=True
        )

        if os.path.exists(
                BGUTIL_SERVER_HOME
        ):

            try:

                print(
                    "BGUTIL directory contents:",
                    os.listdir(
                        BGUTIL_SERVER_HOME
                    ),
                    flush=True
                )

            except Exception as e:

                print(
                    "Could not list BGUTIL directory:",
                    str(e),
                    flush=True
                )

        # ----------------------------------------------------
        # yt-dlp options
        # ----------------------------------------------------

        options = get_ytdlp_options({

            "quiet":
                False,

            "no_warnings":
                False,

            "verbose":
                True,

            "skip_download":
                True

        })

        print(
            "YT-DLP OPTIONS CREATED",
            flush=True
        )

        print(
            "STARTING YT-DLP EXTRACTION NOW",
            flush=True
        )

        # ----------------------------------------------------
        # Extract information
        # ----------------------------------------------------

        with yt_dlp.YoutubeDL(
                options
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        print(
            "YT-DLP EXTRACTION FINISHED",
            flush=True
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
        # Get available formats
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

            qualities.append({

                "format_id":
                    str(format_id),

                "height":
                    int(height),

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
        # Sort lowest to highest
        # ----------------------------------------------------

        qualities.sort(
            key=lambda x:
                x["height"]
        )

        print(
            "Found",
            len(qualities),
            "qualities",
            flush=True
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

        print(
            "",
            flush=True
        )

        print(
            "================================",
            flush=True
        )

        print(
            "INFO ERROR",
            flush=True
        )

        print(
            str(e),
            flush=True
        )

        print(
            "================================",
            flush=True
        )

        print(
            "",
            flush=True
        )

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
        # Create unique file ID
        # ----------------------------------------------------

        file_id = str(
            uuid.uuid4()
        )

        output_template = os.path.join(

            DOWNLOAD_FOLDER,

            file_id + ".%(ext)s"

        )

        print(
            "",
            flush=True
        )

        print(
            "================================",
            flush=True
        )

        print(
            "STARTING DOWNLOAD",
            flush=True
        )

        print(
            "URL:",
            url,
            flush=True
        )

        print(
            "Format:",
            format_id,
            flush=True
        )

        print(
            "File ID:",
            file_id,
            flush=True
        )

        print(
            "================================",
            flush=True
        )

        # ----------------------------------------------------
        # Download options
        # ----------------------------------------------------

        ydl_opts = get_ytdlp_options({

            "format": (
                f"{format_id}+bestaudio/"
                f"{format_id}"
            ),

            "outtmpl":
                output_template,

            "merge_output_format":
                "mp4",

            "quiet":
                False,

            "no_warnings":
                False,

            "verbose":
                True

        })

        print(
            "STARTING YT-DLP DOWNLOAD",
            flush=True
        )

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        with yt_dlp.YoutubeDL(
                ydl_opts
        ) as ydl:

            ydl.extract_info(
                url,
                download=True
            )

        print(
            "YT-DLP DOWNLOAD FINISHED",
            flush=True
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

        print(
            "DOWNLOAD COMPLETE:",
            filename,
            flush=True
        )

        return jsonify({

            "success":
                True,

            "file_id":
                file_id,

            "filename":
                filename

        })

    except Exception as e:

        print(
            "",
            flush=True
        )

        print(
            "================================",
            flush=True
        )

        print(
            "DOWNLOAD ERROR",
            flush=True
        )

        print(
            str(e),
            flush=True
        )

        print(
            "================================",
            flush=True
        )

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
                                    filepath,
                                    flush=True
                                )

                            except Exception as cleanup_error:

                                print(
                                    "Could not delete:",
                                    filepath,
                                    flush=True
                                )

                                print(
                                    cleanup_error,
                                    flush=True
                                )

            except Exception as cleanup_error:

                print(
                    "Partial-file cleanup error:",
                    cleanup_error,
                    flush=True
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

                "success":
                    False,

                "error":
                    "File not found"

            }), 404

        print(
            "SENDING FILE:",
            filepath,
            flush=True
        )

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

        print(
            "FILE ERROR:",
            str(e),
            flush=True
        )

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

                "success":
                    True,

                "message":
                    "File already deleted"

            })

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

        print(
            "TEMPORARY FILE DELETED:",
            filepath,
            flush=True
        )

        return jsonify({

            "success":
                True,

            "message":
                "File deleted successfully"

        })

    except Exception as e:

        print(
            "CLEANUP ERROR:",
            str(e),
            flush=True
        )

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

    print(
        "================================",
        flush=True
    )

    print(
        "YT DOWNLOADER BACKEND",
        flush=True
    )

    print(
        "================================",
        flush=True
    )

    print(
        "Server running on port 5000",
        flush=True
    )

    print(
        "Download folder:",
        os.path.abspath(
            DOWNLOAD_FOLDER
        ),
        flush=True
    )

    print(
        "BGUTIL provider:",
        BGUTIL_SERVER_HOME,
        flush=True
    )

    print(
        "Node.js:",
        "/usr/bin/node",
        flush=True
    )

    print(
        "================================",
        flush=True
    )

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )

