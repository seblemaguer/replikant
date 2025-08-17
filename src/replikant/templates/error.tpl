<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error {{ error_code }}</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                background-color: #fff;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #d9534f;
            }
            .details {
                margin-top: 20px;
                padding: 15px;
                background-color: #f9f9f9;
                border: 2px solid #ddd;
            }
            .details h2 {
                font-size: 1.2em;
                margin-bottom: 5px;
                color: #333;
            }
            .details p {
                margin: 5px 0;
            }
            .stacktrace {
                background-color: #FEFEFE;
                padding: 10px;
                margin: 5px;
                border: 1px solid #ddd;
                overflow-x: auto;
                font-family: monospace;
                font-size: 0.9em;
                white-space: pre;
            }
            .source-url {
                color: #0275d8;
                text-decoration: none;
            }
            .contact {
                margin-top: 30px;
                font-size: 1.1em;
                color: #555;
            }
            .contact a {
                color: #0275d8;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Error {{ error_code }}</h1>

            <div class="contact">
                <p>
                    The platform faced an error. Your progress was not lost but please report the error to <a href="mailto:{{ email }}">{{ authors }}</a>.
                </p>
                <p>
                    While reporting the error, please provide the following details:
                </p>
            </div>


            <div class="details">
                <h2>Local time on the server:</h2>
                <p>{{now}}</p>


                {% if auth.validates_connection("connected")[0] %}
                <h2>User:</h2>
                <p>{{auth.user.user_id}}</p>
                {% endif %}

                <h2>Message:</h2>
                <p>{{ error_message }}</p>

                <h2>Source URL:</h2>
                <p><a class="source-url" href="{{ source_url }}">{{ source_url }}</a></p>

                {% if error_stacktrace %}
                <h2>Stack Trace:</h2>
                <div class="stacktrace">
{{ error_stacktrace }}
                </div>
                {% endif %}
            </div>

        </div>
    </body>
</html>
