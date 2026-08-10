
from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)
print("========================================")
print("YT DOWNLOADER SERVER STARTED")
print("BGUTIL PATH:")
print("/app/bgutil-ytdlp-pot-provider/server")
print("========================================", flush=True)
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


def get_ytdlp_options(extra_options=None):
    """
    Create common yt-dlp options with the bgutil
    PO-token provider configured.
    """

    options = {

        "extractor_args": {

            "youtubepot-bgutilscript": {

                "server_home":
                    BGUTIL_SERVER_HOME

            }

        }

    }

    if extra_options:
        options.update(extra_options)

    return options


# ============================================================
# GET VIDEO INFORMATION
# ============================================================

@app.route("/info", methods=["POST"])
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
        print("YT-DLP VERSION:", yt_dlp.version.__version__, flush=True)
        print("BGUTIL DIRECTORY EXISTS:",os.path.exists("/app/bgutil-ytdlp-pot-provider/server"),
        flush=True
        )
        print("BGUTIL DIRECTORY CONTENTS:",os.listdir("/app/bgutil-ytdlp-pot-provider/server")
        if os.path.exists("/app/bgutil-ytdlp-pot-provider/server")
        else "DIRECTORY NOT FOUND",
        flush=True
        )
        print("================================")

        options = get_ytdlp_options({
            "quiet": False,
            "no_warnings": False,
            "verbose": True,
            "skip_download": True
        })

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
            "qualities"
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

@app.route("/download", methods=["POST"])
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

        print()
        print("================================")
        print("STARTING DOWNLOAD")
        print("================================")
        print("URL:", url)
        print("Format:", format_id)
        print("File ID:", file_id)
        print("================================")
        print()

        # ----------------------------------------------------
        # yt-dlp options
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
                False

        })

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
        # Get filename
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
        # Try deleting
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

    print()
    print("================================")
    print("YT DOWNLOADER BACKEND")
    print("================================")
    print("Server running on port 5000")
    print("Download folder:")
    print(
        os.path.abspath(
            DOWNLOAD_FOLDER
        )
    )
    print("BGUTIL provider:")
    print(
        BGUTIL_SERVER_HOME
    )
    print("================================")
    print()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
