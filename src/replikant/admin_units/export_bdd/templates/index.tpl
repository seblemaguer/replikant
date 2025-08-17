{% extends get_template('base.tpl') %}

{% block content %}

<h2 class="bd-content-title">Download database</h2>
<div class="row">
    <div class="col-6">
        <div class="card" style="margin-bottom:20px;">
            <div class="card-body">
                <h5 class="card-title">ZIP</h5>
                <p class="card-text">Download a zip repository containing the database dumped in csv files and <a href="https://developer.mozilla.org/fr/docs/Web/API/Blob">blob files.</p>
                    <a href="replikant.zip" class="btn btn-primary">Download</a>
            </div>
        </div>
    </div>

    <div class="col-6">
        <div class="card" style="margin-bottom:20px;">
            <div class="card-body">
                <h5 class="card-title">SQLite</h5>
                <p class="card-text">Download the sqlite database</p>
                <a href="replikant.db" class="btn btn-primary">Download</a>
            </div>
        </div>
    </div>
</div>

<a href="{{homepage}}"> Back to admin panel.</a>

{% endblock %}
