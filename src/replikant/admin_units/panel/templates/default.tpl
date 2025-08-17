{% extends get_template('base.tpl') %}

{% block content %}

  <h2 class="bd-content-title">Admin Panel</h2>

  <form action="./login" method="post" class="form-example">
    <div class="form-group">
      <label for="admin_password">Enter the admin password: </label>
      <input type="password" name="admin_password" id="admin_password" class="form-control" required>
    </div>

    <center>
      <button type="submit" class="btn btn-primary">Submit</button>
    </center>
  </form>



{% endblock %}
