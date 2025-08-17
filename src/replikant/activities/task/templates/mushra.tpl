{% extends 'base.tpl' %}

{% block head %}
<style>

    input[type="range"] {
        writing-mode: vertical-lr;
        direction: rtl;
        height: 100%;
    }

    input[type="range"]:hover {
        background: blue;
    }

    .slider-tooltip {
        position: absolute;
        top: -35px;
        left: 0;
        transform: translateX(-50%);
        padding: 5px 10px;
        background-color: #555;
        color: white;
        font-size: 12px;
        border-radius: 5px;
        white-space: nowrap;
    }

    .slider-container {
        height:300px;
    }

    td {
        text-align: center;
    }

    /* Scale container within a table cell */
    .scale-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 0 auto;
    }

    /* Vertical scale bar */
    .scale-bar {
        position: relative;
        height: 300px; /* Adjust height as needed */
        width: 15px;
        background: linear-gradient(#2ecc71, #cccccc, #e74c3c);
    }

    /* Scale divisions */
    .scale-step {
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        height: 2px;
        background-color: #333;
    }

    /* Labels for MUSHRA scale */
    .label-container {
        position: absolute;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        top: 0;
        right: 80px;
        height: 100%;
    }

    .label {
        font-size: 14px;
        color: #333;
        transform: translateY(-50%); /* Center each label in its interval */
        position: absolute;
    }
    /* Position each label at the center of each interval */
    .label:nth-child(1) { top: 10%; }      /* Excellent */
    .label:nth-child(2) { top: 30%; }      /* Good */
    .label:nth-child(3) { top: 50%; }      /* Fair */
    .label:nth-child(4) { top: 70%; }      /* Poor */
    .label:nth-child(5) { top: 90%; }      /* Bad */

    .score_value {
        font-size: 14px;
        background-color: #ddd;
        margin-top: 10px;
        font-weight: bold;
    }
</style>
{% endblock %}

{% block content %}
  {# NOTE: one list to rule them all! (else we potentially generate the list) #}
  {% set samples = list_samples() %}

  {% if (intro_step | default(False, True)) %}
    <div class="alert alert-warning alert-dismissible fade show" role="alert">
      <h4 class="alert-heading">This is the <strong>introduction</strong>.</h4>
      <p>Your answers will <strong>not</strong> be recorded.</p>

      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  {% endif %}

  {% if not((intro_step | default(False, True))) and (step == 1) %}
    <div class="alert alert-danger alert-dismissible fade show" role="alert">
      <h4 class="alert-heading">This is now the <strong>real</strong> test, not an introduction step.</h4>

      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  {% endif %}



  <h2 class="bd-content-title">
    {{subtitle}}
    <div class="progress" style="height: 20px; width:50%; float:right;" >
      <div id="progress-bar" class="progress-bar" role="progressbar"
           style="width: {{(step-1)/max_steps*100}}%;"
           aria-valuenow="{{step-1}}"
           aria-valuemin="0"
           aria-valuemax="{{max_steps}}">
           [{{step-1}} / {{max_steps}}]
      </div>
  </h2>

<form action="./save" method="post" enctype="multipart/form-data" class="form-example" id="the_form">

    <fieldset class="form-group">
        <legend class="col-form-label" style="font-size: large; background-color: #e8f4ea; color: #000; padding: 20px; margin-top: 20px; margin-bottom:20px; border-radius: 25px;">
            {% block instruction %}
            <strong>Question:</strong> How do you judge the <strong>quality</strong> of the following candidates against the reference?
            {% endblock %}
        </legend>

        <div class="form-group" style="margin-bottom:20px;">
            <center>
                {% set content,mimetype = ("", "audio")  %}
                {% block player_view scoped %}
                {% include get_template('players/default/player.html') %}
                {% endblock %}
            </center>
        </div>

        <div class="form-group" style="margin-bottom:20px;">
            <table width="100%">
                <tbody>
                    <tr>
                        <td><b>System</b></td>
                        <td><b><button type="button" class="btn btn-primary btn-mute" id="audio_{{samples|length}}" onclick="selectSample({{samples|length}}, true)">Reference</button></b></td>
                        {% for sample in samples%}
                        {% set name_field = sample | generate_field_name(basename="sample_%d" % loop.index) %}
                        <td>
                            <button type="button" class="btn btn-primary btn-mute" id="audio_{{loop.index-1}}" onclick="selectSample({{loop.index - 1}}, true)">Sample {{loop.index}}</button>
                        </td>
                        {% endfor %}
                    </tr>
                    <tr>
                        <td><b>Fully played?</b></td>
                        <td>
                            <span id="checked_{{samples|length}}" style="display: none; color:green;" />
                        </td>
                        {% for sample in samples %}
                        <td>
                            <span id="checked_{{loop.index-1}}" style="display: none; color:green;" />
                        </td>
                        {% endfor %}
                    </tr>
                    <tr>
                        <td><b>Rank</b></td>
                        <td>
                            <!-- Vertical scale inside a table cell -->
                            <div class="scale-container">
                                <div class="scale-bar">
                                    <div class="scale-step" style="top: 0%;"></div>
                                    <div class="scale-step" style="top: 20%;"></div>
                                    <div class="scale-step" style="top: 40%;"></div>
                                    <div class="scale-step" style="top: 60%;"></div>
                                    <div class="scale-step" style="top: 80%;"></div>
                                    <div class="scale-step" style="top: 100%;"></div>

                                    <!-- Label container for descriptive text -->
                                    <div class="label-container">
                                        <div class="label">Excellent</div>
                                        <div class="label">Good</div>
                                        <div class="label">Fair</div>
                                        <div class="label">Poor</div>
                                        <div class="label">Bad</div>
                                    </div>
                                </div>
                            </div>
                        </td>
                        {% for sample in samples %}
                        {% set name_field = sample | generate_field_name(basename="rank_score_%d" % loop.index) %}
                        <td class="slider-container">
                            <input type="range" id="score_{{loop.index}}" name="{{ name_field }}" class="form-control-range" data-trigger="hover" data-vertical="true" data-toggle="popover" data-content="Fair (50)" data-slider-min="0" data-slider-max="100" data-slider-step="1" data-slider-value="50" oninput="onInputSlider(this)" onmouseup="onMonitorScoring(this)" required />
                        </td>
                        {% endfor %}
                    </tr>

                    <tr>
                        <td></td>
                        <td></td>
                        {% for sample in samples %}
                        <td>
                            <div id="value_{{loop.index}}" class='score_value'>Not scored</div>
                        </td>
                        {% endfor %}
                    </tr>
                </tbody>
            </table>
        </div>

        <center>
            <button type="submit" id="submit" class="btn btn-primary" title="You haven't played all the samples yet">Submit</button>
        </center>
</form>

<script>
    {% block player_controls scoped %}
    {% include get_template('players/default/controls.js') %}
    {% endblock %}

    {% set ref_sample = list_samples(reference_system)[0] %}
    {% set ref_content, ref_mimetype = ref_sample.get("audio") %}

    const list_audios = [
        {% for sample in samples %}
        {% set content,mimetype = sample.get("audio")  %}
        {% if mimetype.startswith("audio") %}
        ["{{sample}}", "{{content}}"],
        {% endif %}
        {% endfor %}
        {% if ref_mimetype.startswith("audio") %}
        ["{{ref_sample}}", "{{ref_content}}"]
        {% endif %}

    ];

    const labels = ['Bad', 'Poor', 'Fair', 'Good', 'Excellent'];
    const colors = ['#e74c3c', '#cccccc', '#2ecc71']; // Gradient colors

    const URL_MONITOR =  window.location.href + "monitor";
    const monitor_handler = async (action, value, sample_id) => {
        const body = {
            "sample_id": sample_id,
            "info_type": action,
            "info_value": value
        }

        // FIXME: the URL needs to be generalised (both base part & stage part)
        const response = await fetch(URL_MONITOR, {
            method: 'POST',
            body: JSON.stringify(body),
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    var played_audios = new Set();
    var scored_audios = new Set();
    var cur_sample_index = -1;
    var cur_selected_audio_btn = null;

    function getGradientColor(minColor, midColor, maxColor, value, min, max) {
        const interpolate = (start, end, factor) => Math.round(start + (end - start) * factor);
        const parseColor = (hex) => hex.match(/#(..)(..)(..)/).slice(1).map(c => parseInt(c, 16));

        const [minR, minG, minB] = parseColor(minColor);
        const [midR, midG, midB] = parseColor(midColor);
        const [maxR, maxG, maxB] = parseColor(maxColor);

        const midPoint = (max + min) / 2;

        if (value <= midPoint) {
            const factor = (value - min) / (midPoint - min);
            return `rgb(${interpolate(minR, midR, factor)}, ${interpolate(minG, midG, factor)}, ${interpolate(minB, midB, factor)})`;
        } else {
            const factor = (value - midPoint) / (max - midPoint);
            return `rgb(${interpolate(midR, maxR, factor)}, ${interpolate(midG, maxG, factor)}, ${interpolate(midB, maxB, factor)})`;
        }
    }

    function onInputSlider(slider) {
        const value = parseInt(slider.value);
        slider.style.setProperty('accent-color', getGradientColor(colors[0], colors[1], colors[2], value, 0, 100));
        const label = labels[Math.min(Math.floor(value / 20), labels.length-1)];
        const id = parseInt(slider.id.split("_")[1]);
        const label_elt = document.getElementById(`value_${id}`);
        label_elt.innerHTML = `${value} (${label})`;
        scored_audios.add(`value_${id}`);

        // Enable the submit button if all audios have been played
        if ((played_audios.size === list_audios.length) &&
            (scored_audios.size === (list_audios.length - 1))) {
            document.getElementById('submit').disabled = false;
        }

    }
    function onMonitorScoring(slider) {
        console.log(slider.name.split(":").slice(-1)[0]);
        monitor_handler("score_sample", slider.value, slider.name.split(":").slice(-1)[0]);
    }

    function selectSample(index, play) {
        if (cur_sample_index >= 0) {
           monitor_handler("switch_sample", [`sampleid:${list_audios[index][0]}`,  audio.currentTime], list_audios[cur_sample_index][0]);
        }

        audio_source.src = list_audios[index][1];
        audio.load();
        cur_sample_index = index;

        // Update button to reflect the new status
        if (cur_selected_audio_btn) {
            cur_selected_audio_btn.disabled = false;
            cur_selected_audio_btn.classList.replace("btn-solo", "btn-mute");
        }

        cur_selected_audio_btn = document.getElementById("audio_" + index);
        cur_selected_audio_btn.disabled = true;
        cur_selected_audio_btn.classList.replace("btn-mute", "btn-solo");

        if (play) {
            audio.play()
        }
    }

    audio.addEventListener("pause", function (){
        if (audio.currentTime < audio.duration) {
            monitor_handler("pause", audio.currentTime, list_audios[cur_sample_index][0]);
        } else {
            monitor_handler("ended", audio.currentTime, list_audios[cur_sample_index][0]);
        }
    });

    audio.addEventListener("play", function (){
        monitor_handler("play", audio.currentTime, list_audios[cur_sample_index][0]);
    });

    audio.addEventListener("ended", function(){
        played_audios.add(cur_sample_index);

        var checked = document.getElementById("checked_" + cur_sample_index);
        checked.textContent = "✔";
        checked.style.display = "";

        // Enable the submit button if all audios have been played
        if ((played_audios.size === list_audios.length) &&
            (scored_audios.size === (list_audios.length - 1))) {
            console.log(`${scored_audios.size} ?= ${list_audios.length}`)
            document.getElementById('submit').disabled = false;
        }
    });

    // Initially disable the submit button
    document.getElementById('submit').disabled = true;
    selectSample(list_audios.length-1, false);
</script>
{% endblock %}
