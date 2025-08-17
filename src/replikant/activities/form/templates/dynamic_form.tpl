{% extends get_template('base.tpl') %}

{% block content %}

{% set form_json = form_json_data%}

<h2 class="bd-content-title"> {{form_json["title"]}}</h2>


<form action="./save" method="post" class="form-example">

  {% for component in form_json["components"] %}
    <div class="form-group">
      <label for="name">{{component["label"]}}</label>
      <input type="{{component['input']['type']}}" name="{{component['id']}}" id="{{component['id']}}" class="form-control" required>
    </div>
  {% endfor %}

  <button type="submit" class="btn btn-primary">Submit</button>

</form>


{% endblock %}
