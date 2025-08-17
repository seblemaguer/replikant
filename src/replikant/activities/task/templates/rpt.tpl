{% extends get_template('base.tpl') %}

{% block head %}
  <style>

    .word, .boundary {
    display: inline-block;
    margin-right: 5px;
    padding: 5px 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    background-color: #f4f4f4;
    cursor: pointer;
    transition: background-color 0.3s, transform 0.2s;
    }

    .word:hover, .boundary:hover {
    background-color: #d1ecf1;
    transform: scale(1.1);
    }

    .selected {
    background-color: #f8d7da; /* Pastel red */
    border-color: #f5c2c7;
    }
    fieldset {
    border: 1px solid #c0c0c0;
    margin: 0 2em 0 0;
    padding: 0.5em;
    }
    legend {
    display: block;
    width: auto;
    max-width: 100%;
    padding: 0 0.5em 0 0.5em;
    margin-bottom: .5rem;
    font-size: 1.5rem;
    line-height: inherit;
    color: inherit;
    white-space: normal;
    }

  </style>
{% endblock %}

{% block content %}
  {% if (intro_step | default(False, True)) %}
    <div class="alert alert-warning alert-dismissible fade show" role="alert">
      <h4 class="alert-heading">This is the <strong>introduction</strong>.</h4>
      <p>Your answers will <strong>not</strong> be recorded as correct answer.</p>

      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  {% endif %}

  {% if not((intro_step | default(False, True))) and (step == 1) %}
    <div class="alert alert-danger alert-dismissible fade show" role="alert">
      <h4 class="alert-heading">This is now the <strong>real</strong> test, not an introduction step.</h4>

      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  {% endif %}


  <h2 class="bd-content-title">
    Step {{step}} over {{max_steps}}
  </h2>

  <form action="./save" method="post" enctype="multipart/form-data" class="form-example">

      {% set sample = list_samples[0] %}
      <div class="form-group" style="margin-bottom:10px;">
        {% set name_field = sample | generate_field_name(name="MOS_score") %}
        {% set content, mimetype = sample.get('audio')  %}

        <div id="player_area" style="margin-bottom:10px;">
          <center>
            {% block player_view scoped %}
              {% include get_template('players/default/player.html') %}
            {% endblock %}
          </center>
        </div>

        {# Rapid Prosody Transcription Part #}
        <div id="rpt_area" style="margin-bottom:10px;">
          <fieldset>
            <legend>Rapid Prosody Transcription</legend>

            <center>
              <div id="text-container"></div>
            </center>
            <input type="hidden" id="selected-items" name="selected_items" value="">
          </fieldset>
        </div>

        {# MOS Part #}
        <div id="mos_area" style="margin-bottom:10px;">
          <fieldset>
            <legend>Mean Opinion Score</legend>
            {% block mos_instruction %}
              How natural is the speaker’s intonation?
              The scale is from <b>1 [Completely Unnatural] to 5 [Completely Natural]</b>.
            {% endblock %}

            <select id="mos_score@{{sample.ID}}" name="{{name_field}}" class="form-control" required>
              <option value="" selected disabled hidden>Choose here</option>
              {% block score_options %}
                <option value="1">1 : Completely Unnatural</option>
                <option value="2">2 : Mostly Unnatural</option>
                <option value="3">3 : Equally Natural and Unnatural</option>
                <option value="4">4 : Mostly Natural</option>
                <option value="5">5 : Completely Natural</option>
            {% endblock %}
            </select>
          </fieldset>
        </div>

        {# Qualification Part #}
        <div id="error_type_area" style="margin-bottom:10px;">
          <fieldset>
            <legend>Error type(s)</legend>
            {% block error_type_instruction %}
              Please pick the types of errors you noticed (None if no errors)
            {% endblock %}

            <ul>
              {# NOTE: this is used as a backup to remind me to implement this in the server side #}
              {# <li><input type="checkbox" name="error_type@{{sample.ID}}[]" id="abrupt@{{sample.ID}}" value="Abrupt change in pitch">Abrupt change in pitch</input></li> #}
              {# <li><input type="checkbox" name="error_type@{{sample.ID}}[]" id="pause@{{sample.ID}}" value="Awkward pause">Awkward pause</input></li> #}
              {# <li><input type="checkbox" name="error_type@{{sample.ID}}[]" id="unexpected@{{sample.ID}}" value="Unexpected intonation">Unexpected intonation</input></li> #}
              {# <li><input type="checkbox" name="error_type@{{sample.ID}}[]" id="lack@{{sample.ID}}" value="Lacking intonation">Lacking intonation</input></li> #}
              {# <li><input type="checkbox" name="error_type@{{sample.ID}}[]" id="no@{{sample.ID}}" value="None">None</input></li> #}

              {% set name_field = sample | generate_field_name(basename="abrupt_change") %}
              <li><input type="checkbox" id="abrupt@{{sample.ID}}" name="{{name_field}}" value="True">Abrupt change in pitch</input></li>

              {% set name_field = sample | generate_field_name(basename="awkward_pause") %}
              <li><input type="checkbox" id="pause@{{sample.ID}}" name="{{name_field}}" value="True">Awkward pause</input></li>

              {% set name_field = sample | generate_field_name(basename="unexpected_intonation") %}
              <li><input type="checkbox" id="unexpected@{{sample.ID}}" name="{{name_field}}" value="True">Unexpected intonation</input></li>

              {% set name_field = sample | generate_field_name(basename="lacking_intonation") %}
              <li><input type="checkbox" id="lack@{{sample.ID}}" name="{{name_field}}" value="True">Lacking intonation</input></li>

              <li><input type="checkbox" id="no@{{sample.ID}}" value="None">None</input></li>
            </ul>
          </fieldset>
        </div>
      </div>

      <center>
        <button type="submit" id="submit" class="btn btn-primary">Submit</button>
      </center>
  </form>

  <script>
    {% block player_controls scoped %}
      {% include get_template('players/default/controls.js') %}
    {% endblock %}

    //
    {% set text_content, ignored = sample.get('text') %}
    const text = '{{text_content}}';
    const selectedItems = [];
    const textContainer = document.getElementById("text-container");
    const selectedItemsField = document.getElementById("selected-items");

    function updateSelectedList() {
    	// Sort by original index to maintain presentation order
    	selectedItems.sort((a, b) => a.index - b.index);
    	selectedItemsField.value = selectedItems.map(({ item }) => item).join(",");
    }

    // Function to toggle selection and maintain original order
    function toggleSelection(element, item, index) {
    	const existingIndex = selectedItems.findIndex(el => el.item === item);
    	if (existingIndex > -1) {
            // If already selected, remove it
    	    selectedItems.splice(existingIndex, 1);
    	    element.classList.remove("selected");
    	} else {
            // Otherwise, add it with the original index
            selectedItems.push({ item, index });
            element.classList.add("selected");
        }

        updateSelectedList();
    }

    // Split text into words and boundaries
    const regex = /([\w'-]+|[.,!?])/g; // Match words or boundaries
    const matches = text.match(regex);

    matches.forEach((match, index) => {
        const element = document.createElement("span");
        element.textContent = match;
        element.className = /[.,!?]/.test(match) ? "boundary" : "word"; // Boundary or word class
        element.onclick = () => toggleSelection(element, match, index); // Pass index
        textContainer.appendChild(element);
    });
  </script>
{% endblock %}
