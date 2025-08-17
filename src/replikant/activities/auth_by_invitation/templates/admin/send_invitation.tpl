{% extends get_template('base.tpl') %}

{% block head %}
<script>
$(document).ready(function(){

  $("#email_content").html($("#message").val())
  $("#email_title").html($("#title_message").val())

  // Read value on change
  $("#message").on("focus mouseleave change click",function(){
    $("#email_content").html($("#message").val())
  });

  $("#title_message").on("focus mouseleave change click",function(){
    $("#email_title").html($("#title_message").val())
  });

});

</script>
{% endblock %}

{% block content %}
  <h2 class="bd-content-title">Send Invitation</h2>


  <form action="./send_invitation/send" method="post" class="form-example">
    <div class="form-group">
      <label for="emails">List of emails for which you want to send an invitation (separated them with a comma). </label>
      <input type="email" name="emails" id="emails" class="form-control" multiple required>

      <label for="title_message">Title</label>
      <input type="text" name="title_message" id="title_message" class="form-control" value="Invitation" required>


      <label for="message">Message</label>
      <textarea rows="10" name="message" id="message" class="form-control" required>
Hello,
If you want to help me, by completing a survey, please click on the link below.
Thanks for your time - Cédric Fayet.

NB: In order to handle this invitation, we have saved your email in our database.
For more information concerning our right follow this link: <a href="{{make_url('/legal_terms')}}">{{make_url('/legal_terms')}}</a>
       </textarea>

    </div>

    <button type="submit" class="btn btn-primary">Send</button>

  </form>

  <h3 class="bd-content-title">Overview</h3>
  <p><strong>Title: </strong> <div id="email_title"></div></p>
  <p>
    <strong>Content: </strong>
    <pre>
<div id="email_content"></div>
<a href="#">{{make_url("/?token=SuperSecretToken")}}</a>
    </pre>
  </p>

  <a href="./"> Back</a>

{% endblock %}
