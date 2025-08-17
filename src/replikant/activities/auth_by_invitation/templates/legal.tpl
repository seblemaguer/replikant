{% extends get_template('base.tpl') %}

{% block content %}
  <h2 class="bd-content-title">Legal terms</h2>
  <form action="./register?{{get_variable('token')}}" method="post" class="form-example">

    <div class="form-check">
      <input type="checkbox" class="form-check-input" id="legalterms" required>
      <label class="form-check-label" for="legalterms">I acknowledge having read and accept <a href="{{make_url('/legal_terms')}}">the GCUs and the privacy policy</a>.</label>
    </div>

    <button type="submit" class="btn btn-primary">Submit</button>

  </form>
{% endblock %}
