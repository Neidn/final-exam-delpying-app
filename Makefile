# make makemigrations
makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

runserver:
	python manage.py runserver


.PHONY: makemigrations migrate runserver
