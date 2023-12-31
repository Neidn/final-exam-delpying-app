from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import *
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
def index(request):
    context = {}
    courses = Course.objects.all()
    context['courses'] = courses
    return render(request, 'onlinecourse/index.html', context)


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)

    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def submit(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)

    selected_choice_ids = []

    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            selected_choice_ids.append(choice_id)

    for choice_id in selected_choice_ids:
        choice = Choice.objects.get(pk=choice_id)
        submission.choices.add(choice)

    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id, submission.id,)))


# def extract_answers(request):
#     submitted_answers = []
#
#     for key, value in request.POST.items():
#         if key.startswith('choice'):
#             choice_id = int(value)
#             submitted_answers.append(choice_id)
#
#     return submitted_answers


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = Submission.objects.get(pk=submission_id)
    choice_ids = submission.choices.values_list('pk', flat=True)

    total_score = 0
    selected_choice_ids = []

    for choice_id in choice_ids:
        choice = Choice.objects.get(pk=choice_id)
        selected_choice_ids.append(choice)

        if choice.is_correct:
            total_score += 1

    grade = total_score / len(choice_ids) * 100 if len(choice_ids) > 0 else 0

    # Convert to int
    grade = int(grade)

    context = {
        'course': course,
        'submission': submission,
        'selected_choice_ids': selected_choice_ids,
        'total_score': total_score,
        'grade': grade,
    }

    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
