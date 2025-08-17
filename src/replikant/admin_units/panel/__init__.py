# coding: utf8
# license : CeCILL-C

from flask import request

from replikant.core import campaign_instance
from replikant.core import AdminScope
from replikant.utils import redirect, make_global_url

from .provider import AdminAuthProvider

AdminScope.set_auth_provider(AdminAuthProvider)

with campaign_instance.register_admin_unit(__name__) as am:

    @am.route("/", methods=["GET"])
    def main():
        authProvider = am.auth_provider

        if authProvider.validates_connection("connected")[0]:
            return redirect(am.url_for(am.get_endpoint_for_local_rule("/panel")))
        else:
            return redirect(am.url_for(am.get_endpoint_for_local_rule("/auth")))

    @am.route("/auth", methods=["GET"])
    def auth():
        return am.render_template()

    @am.route("/login", methods=["POST"])
    def login():
        password = request.form["admin_password"]
        config = am.get_config()
        assert config is not None
        master_password = config["password"]

        if password == master_password:
            assert isinstance(am.auth_provider, AdminAuthProvider)
            am.auth_provider.connect()
            return redirect(am.url_for(am.get_endpoint_for_local_rule("/panel")))
        else:
            return redirect(am.url_for(am.get_endpoint_for_local_rule("/")))

    @am.route("/panel", methods=["GET"])
    @am.valid_connection_required
    def panel():
        admin_units = []

        for mod_name, mod in campaign_instance.get_admin_units().items():
            if am != mod:
                config_mod = mod.get_config()
                assert config_mod is not None
                title = mod_name
                description = ""
                if "variables" in config_mod:
                    if "subtitle" in config_mod["variables"]:
                        title = config_mod["variables"]["subtitle"]

                    if "subdescription" in config_mod["variables"]:
                        description = config_mod["variables"]["subdescription"]

                admin_unit = {
                    "title": title,
                    "description": description,
                    "url": make_global_url("/" + mod.local_url()),
                }

                admin_units.append(admin_unit)

        variables = dict()
        variables["admin_units"] = admin_units
        return am.render_template(path_template="panels.tpl", variables=variables)
