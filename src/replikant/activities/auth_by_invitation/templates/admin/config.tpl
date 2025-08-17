{% extends get_template('base.tpl') %}

{% block content %}
  <h2 class="bd-content-title">Configuration</h2>

  {% if (false_credential | default(False, True)) %}
    <div class="alert alert-danger alert-dismissible fade show" role="alert">
      <strong>Bad Credentials !</strong> With the information below, the server can't contact your mail server.
      There are two main reasons: the information provided are incorrect, or your mail server used a 2-steps verification.
      In this case, you need to create an app-specific password.
      For gmail, you will find information by <a href="https://support.google.com/accounts/answer/185833?hl=en"> following this link.</a>
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  {% endif %}

  <p> Register the configuration of your email box. These information will be used to send our invitation.</p>
  <form action="./configuration/update" method="post" class="form-example">
    <div class="form-group">
      <label for="MAIL_SERVER"> Mail Server </label>
      <input type="text" name="MAIL_SERVER" id="MAIL_SERVER" class="form-control" value="{{MAIL_SERVER}}">

      <label for="MAIL_PORT"> Mail Port</label>
      <input type="number" name="MAIL_PORT" id="MAIL_PORT" class="form-control" value="{{MAIL_PORT}}">

      <label for="MAIL_USE_TLS"> Mail Server Use TLS ?</label>
      <input type="checkbox" name="MAIL_USE_TLS" id="MAIL_USE_TLS" class="form-control" {% if MAIL_USE_TLS %} checked {% endif %}>

    <div class="form-group">
      <label for="MAIL_USERNAME"> Username</label>
      <input type="email" name="MAIL_USERNAME" id="MAIL_USERNAME" class="form-control" value="{{MAIL_USERNAME}}">

      <label for="MAIL_PASSWORD"> Password</label>
      <input type="password" name="MAIL_PASSWORD" id="MAIL_PASSWORD" class="form-control" value="{{MAIL_PASSWORD}}">
    </div>
    <button type="submit" class="btn btn-primary">Send</button>

  </form>

  <p><a href="./"> Back</a></p>

{% endblock %}
