"""Тесты для Django-приложения с курсами и списком студентов."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from model_bakery import baker
from students.models import Course, Student


@pytest.fixture
def api_client():
    """Возвращает экземпляр тестового API-клиента."""
    return APIClient()


@pytest.fixture
def course_factory():
    """Фабрика для создания объектов Course через model_bakery."""
    def factory(**kwargs):
        return baker.make(Course, **kwargs)
    return factory


@pytest.fixture
def student_factory():
    """Фабрика для создания объектов Student через model_bakery."""
    def factory(**kwargs):
        return baker.make(Student, **kwargs)
    return factory


@pytest.mark.django_db
def test_retrieve_first_course(api_client, course_factory):
    """Проверка получения первого курса (retrieve-логика)."""
    courses = course_factory(_quantity=3)
    first_course = courses[0]
    url = reverse("courses-detail", args=[first_course.id])

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == first_course.id
    assert response.data["name"] == first_course.name


@pytest.mark.django_db
def test_list_courses(api_client, course_factory):
    """Проверка получения списка курсов (list-логика)."""
    courses = course_factory(_quantity=5)
    url = reverse("courses-list")

    response = api_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == len(courses)

    response_ids = {item["id"] for item in response.data}
    expected_ids = {course.id for course in courses}
    assert response_ids == expected_ids


@pytest.mark.django_db
def test_filter_courses_by_id(api_client, course_factory):
    """Проверка фильтрации списка курсов по ID."""
    courses = course_factory(_quantity=5)
    target_course = courses[2]
    url = reverse("courses-list")

    response = api_client.get(url, data={"id": target_course.id})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == target_course.id


@pytest.mark.django_db
def test_filter_courses_by_name(api_client, course_factory):
    """Проверка фильтрации списка курсов по названию (name)."""
    course_factory(name="Django ORM")
    course_factory(name="REST framework")
    course_factory(name="Docker basics")
    url = reverse("courses-list")

    response = api_client.get(url, data={"name": "Django ORM"})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["name"] == "Django ORM"


@pytest.mark.django_db
def test_create_course(api_client):
    """Тест успешного создания курса."""
    url = reverse("courses-list")
    payload = {"name": "New course", "students": []}

    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == 201
    assert response.data["name"] == payload["name"]
    # Проверяем, что объект действительно появился в БД
    assert Course.objects.filter(name=payload["name"]).exists()


@pytest.mark.django_db
def test_update_course(api_client, course_factory):
    """Тест успешного обновления курса."""
    course = course_factory(name="Old name")
    url = reverse("courses-detail", args=[course.id])
    payload = {"name": "Updated name"}

    response = api_client.patch(url, data=payload, format="json")

    assert response.status_code == 200
    assert response.data["name"] == payload["name"]
    # Проверяем обновление непосредственно в БД
    course.refresh_from_db()
    assert course.name == payload["name"]


@pytest.mark.django_db
def test_delete_course(api_client, course_factory):
    """Тест успешного удаления курса."""
    course = course_factory(name="Course to delete")
    url = reverse("courses-detail", args=[course.id])

    response = api_client.delete(url)

    assert response.status_code == 204
    # Проверяем, что объект действительно удалён из БД
    assert not Course.objects.filter(id=course.id).exists()
