# Replikant


Replikant is a python toolkit which aims to enable researcher to develop their own subjective evaluation recipes.
It relies on Flask, Jinja2 and SQLite, and is a refactoring of FlexEval.

I am currently doing some final important cleaning part which I thought would be done by now, but requires a bit more time.


## How to install

Replikant has been tested on python 3.11.

To install the current stable version, run the following command:

```sh
pip install replikant
```

To install the current unstable version, run the following command:

```sh
pip install git+https://github.com/seblemaguer/replikant.git
```

## Developping and running a recipe

### Defining an recipe

The easiest is to start with one of the available recipes and adapt it to your needs.

Here is a list of already available recipes of published studies:
  - https://github.com/sigmedia/bc_2013_extension/tree/master/evaluation/2013-EH2_EXT (MOS - naturalness, similarity; Intelligibility)
  - https://github.com/sigmedia/bc_2013_extension/tree/master/evaluation/mushra (MUSHRA test)
  - https://github.com/sigmedia/bc_2013_extension/tree/master/evaluation/ranked-choice-voting (Ranked Choice Voting)



### Launching a recipe

Simply run :

```sh
replikant <path_configuration_recipe.yaml>
```

By default, the evaluation will be available at: http://127.0.0.1:8080.

The overall behaviour of replikant can be controlled from the command call. Here are the options:
```
usage: replikant [-h] [-d] [-i IP] [-p PORT] [-P] [-t] [-u URL] [-l LOG_FILE] [-v] RECIPE_CONFIGURATION

Replikant

positional arguments:
  RECIPE_CONFIGURATION  Recipe's configuration file

options:
  -h, --help            show this help message and exit
  -d, --debug           Start the server in debugging mode
  -i IP, --ip IP        IP's server
  -p PORT, --port PORT  port
  -P, --production      Start the server in production mode
  -t, --threaded        Enable threads.
  -u URL, --url URL     URL of the server (needed for flask redirections!) if different from http://<ip>:<port>/
  -l LOG_FILE, --log_file LOG_FILE
                        Logger file
  -v, --verbosity       increase output verbosity
```

## Contributing


If you want to participate to the development, you can install the necessary packages using:

```sh
pip install -e .[dev]
```

You then need to activate the pre-commit git hooks:

```sh
pre-commit install
```

## Citing

```bibtex
@inproceedings{lemaguer25_interspeech,
  title     = {Enabling the replicability of speech synthesis perceptual evaluations},
  author    = {Sébastien {Le Maguer} and Gwénolé Lecorvé and Damien Lolive and Naomi Harte and Juraj Šimko},
  year      = {2025},
  booktitle = {Interspeech 2025},
  pages     = {2545--2549},
  doi       = {10.21437/Interspeech.2025-401},
  issn      = {2958-1796},
}
```
