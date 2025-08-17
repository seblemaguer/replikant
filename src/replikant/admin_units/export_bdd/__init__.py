# coding: utf8
# license : CeCILL-C

# Import Libraries
import string
import random
import shutil

from werkzeug import Response
from flask import current_app, send_file

from replikant.core import campaign_instance
from replikant.utils import safe_make_dir
from replikant.database import extract_dataframes

with campaign_instance.register_admin_unit(__name__) as am:
    safe_make_dir(current_app.config["REPLIKANT_RECIPE_TMP_DIR"] + "/export_bdd/")

    # Routes
    @am.route("/")
    @am.valid_connection_required
    def panel():
        return am.render_template("index.tpl")

    @am.route("/replikant.db")
    @am.valid_connection_required
    def sqlite():
        return send_file(current_app.config["SQLALCHEMY_FILE"])

    @am.after_request
    def set_response_headers(response: Response) -> Response:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @am.route("/replikant.zip")
    @am.valid_connection_required
    def zip():
        repository_name = "".join((random.choice(string.ascii_lowercase) for _ in range(15)))
        root_base_file = current_app.config["REPLIKANT_RECIPE_TMP_DIR"] + f"/export_bdd/{repository_name}"

        # Connect to the database
        _ = safe_make_dir(f"{current_app.config['REPLIKANT_RECIPE_TMP_DIR']}/{root_base_file}.bdd")

        # Extract the dataframes
        db_frames = extract_dataframes()

        # Save the TSV file
        for name_table, df in db_frames.items():
            table_fn = f"{current_app.config['REPLIKANT_RECIPE_TMP_DIR']}/{root_base_file}.bdd/{name_table}.tsv"
            df.to_csv(table_fn, sep="\t", index=False)

        # Generate the archive and return it!
        shutil.make_archive(
            base_name=f"{current_app.config['REPLIKANT_RECIPE_TMP_DIR']}/replikant",
            format="zip",
            root_dir=f"{current_app.config['REPLIKANT_RECIPE_TMP_DIR']}/{root_base_file}.bdd",
        )
        shutil.rmtree(f"{current_app.config['REPLIKANT_RECIPE_TMP_DIR']}/{root_base_file}.bdd")

        return send_file(f"{current_app.config['REPLIKANT_RECIPE_TMP_DIR']}/replikant.zip")
