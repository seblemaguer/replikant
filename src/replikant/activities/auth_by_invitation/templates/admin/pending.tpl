{% extends get_template('base.tpl') %}

{% block content %}
  <h2 class="bd-content-title">Pending Invitation</h2>

  <p> An invitation is pending, until the receiver click on the invitation link.</p>
  <table class="table table-hover">
    <thead>
      <tr>
        <th scope="col">Email</th>
        <th scope="col">Pending?</th>
      </tr>
    </thead>
    <tbody>
      {% for w in users%}
      <tr>
        <th>{{w.id}}</th>
        <td>{% if w.active %}No{% else %}Yes{% endif %}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <p><a href="./"> Back</a></p>

{% endblock %}
