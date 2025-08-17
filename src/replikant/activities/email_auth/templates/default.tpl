{% extends get_template('base.tpl') %}

{% block content %}
  <form action="./register" method="post" class="form-example">
    {% block instructions %}
      <h2 class="bd-content-title">Login</h2>
    <p>
      Welcome to the platform.
      Please authenticate using your email.
    </p>
  {% endblock %}

  <div class="mb-3">
    <label for="email">Enter your email: </label>
    <input type="email" name="email" id="email" class="form-control" required>
  </div>

  <button type="submit" class="btn btn-primary" id="login_submit">Submit</button>
  </form>
{% endblock %}
