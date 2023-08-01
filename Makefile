# make makemigrations
makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

runserver:
	python manage.py runserver

super:
	python manage.py createsuperuser


.PHONY: makemigrations migrate runserver super
