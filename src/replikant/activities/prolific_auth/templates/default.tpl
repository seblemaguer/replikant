{% extends 'base.tpl' %}

{% block head %}
  <style>

    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5); /* Pastel red */
        z-index: 9999;
    display: none;
    backdrop-filter: blur(10px); /* Adjust the blur amount as needed */
    }

    .overlay-content {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: white;
        padding: 20px;
        border-radius: 10px; /* Rounded corners */
        border-style: dotted;
        border-color: rgba(254,181,177,1.00);
    border: 10px;
    text-align: center;
    font-size: xx-large;
    }

    .overlay-title {
        font-weight: bold;
        margin-bottom: 10px;
    font-size: xx-large;
    }
</style>
{% endblock %}

{% block content %}
  <form action="./register" method="post" class="form-example justified">

    <input type="hidden" id="PROLIFIC_PID" name="PROLIFIC_PID" value="">
    <input type="hidden" id="STUDY_ID" name="STUDY_ID" value="">
    <input type="hidden" id="SESSION_ID" name="SESSION_ID" value="">

    {% block instructions %}
      <h3>Start or resume the test</h3>
    {% endblock %}

    <br />
    <center>
      <button type="submit" id="login_submit" class="btn btn-primary">Start/Resume the test</button>
    </center>
  </form>


  <div class="overlay" id="overlay">
    <div class="overlay-content">
      <div class="overlay-title">⚠️ There is a problem ⚠️</div>
      <p>You can't participate to this evaluation if you haven't been recruited by Prolific.</p>
    </div>
  </div>


  <script>
    function showOverlay() {
      overlay.style.display = "block";
      document.body.style.pointerEvents = "none";
    }

    window.onload = function() {
      // Extract the variable from the URL
      var urlParams = new URLSearchParams(window.location.search);
      var prolific_pid = urlParams.get('PROLIFIC_PID');
      var study_id = urlParams.get('STUDY_ID');
      var session_id = urlParams.get('SESSION_ID');

      if ((!study_id) || (!prolific_pid) || (!session_id)) {
        showOverlay();
      }

      // Populate the hidden input field with the extracted variable value
      document.getElementById('PROLIFIC_PID').value = prolific_pid;
      document.getElementById('STUDY_ID').value = study_id;
      document.getElementById('SESSION_ID').value = session_id;
    }
  </script>
{% endblock %}
