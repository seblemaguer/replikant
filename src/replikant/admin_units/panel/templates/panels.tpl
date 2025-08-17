{% extends get_template('base.tpl') %}

{% block content %}
<h2 class="bd-content-title">Admin Panel</h2>
<div class="row">
    {% for admin_unit in admin_units%}
    <div class="col-6">
        <div class="card" style="margin-bottom:20px;">
            <div class="card-body">
                <h5 class="card-title">{{admin_unit.title}}</h5>
                <p class="card-text">{{admin_unit.description}}</p>
                <a href="{{admin_unit.url}}" class="btn btn-primary">Access</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
