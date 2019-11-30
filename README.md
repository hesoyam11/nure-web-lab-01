# nure-web-lab-01

A Java web programming lab. The teacher was so kind that he allowed me to write this lab in Python.

## Setup & Run

Create a role and a database in PostgreSQL:
```bash
sudo -u postgres psql -f db_setup.sql
```

Install dependencies and activate virtualenv:
```bash
pipenv install
pipenv shell
```

Configure environment variables:
```bash
export PYTHONPATH=nure_web_lab
export FLASK_APP=nure_web_lab FLASK_ENV=development
```

Create database tables:
```bash
flask init-db
```

Run the server:

```bash
flask run
```

Type `exit` to close the `pipenv`'s shell.
