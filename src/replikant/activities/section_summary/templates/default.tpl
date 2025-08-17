{% extends get_template('base.tpl') %}

{% block head %}
  <style>
      .section {
          margin-top: 20px;
          margin-bottom: 40px;
      }
  </style>
{% endblock %}
{% block content %}
  <h2 class="bd-content-title">
      <img src="{{get_asset('/img/svg_icon/chevron-right.svg', 'replikant')}}" alt=">" />
      Summary
  </h2>

  {% for section_name in list_task_sections %}
    <div class="section">
      <h3>{{section_information[section_name]['label']}}</h3>

      <div class="container mt-4">
        <div class="d-flex align-items-center">
          <!-- Button on the left -->
          {% if (section_information[section_name]['cur_step'] < section_information[section_name]['max_steps']) %}
            <a href="{{section_information[section_name]['url']}}" class="btn btn-primary me-3" role="button" aria-pressed="true">Start/ Resume</a>
          {% else %}
            <a href="{{section_information[section_name]['url']}}" class="btn btn-primary me-3 disabled" role="button" aria-disabled="true" style="pointer-events: none">Start/ Resume</a>
          {% endif %}

          <!-- Progress Bar in the center -->
          <div class="flex-grow-1">
            <div class="progress">
                <div id="progress-bar" class="progress-bar" role="progressbar"
                     style="width: {{section_information[section_name]['cur_step']*100.0/section_information[section_name]['max_steps']}}%;"
                     aria-valuenow="{{section_information[section_name]['cur_step']*100.0/section_information[section_name]['max_steps']}}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
          </div>

          <!-- Label on the right -->
          <span class="ms-3"><span id="current">{{section_information[section_name]['cur_step']}}</span>/{{section_information[section_name]['max_steps']}}</span>
        </div>
      </div>
    </div>
  {% endfor %}

{% endblock %}
