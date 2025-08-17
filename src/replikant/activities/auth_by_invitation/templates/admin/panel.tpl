{% extends get_template('base.tpl') %}

{% block content %}
  <h2 class="bd-content-title">Member</h2>

  <p> Without invitation people can't join this website.</p>

  <div class="row">

    <div class="col-6">

      <div class="card" style="margin-bottom:20px;">
        <div class="card-body">
          <h5 class="card-title">Invitation</h5>
          <p class="card-text">Send an invitation by email.</p>
          <a href="./send_invitation" class="btn btn-primary">Access</a>
        </div>
      </div>
    </div>

    <div class="col-6">

      <div class="card" style="margin-bottom:20px;">
        <div class="card-body">
          <h5 class="card-title">Configuration</h5>
          <p class="card-text">To be able to send invitations you need to configure our mail box.</p>
          <a href="./configuration" class="btn btn-primary">Configure</a>
        </div>
      </div>
    </div>

    <div class="col-6">

      <div class="card" style="margin-bottom:20px;">
        <div class="card-body">
          <h5 class="card-title">Pending Invitations</h5>
          <p class="card-text"> List of all the invitation send.</p>
          <a href="./pending_invitation" class="btn btn-primary">Access</a>
        </div>
      </div>
    </div>

  </div>

  <a href="{{make_url('/admin') }}"> Back to admin panel.</a>

{% endblock %}
