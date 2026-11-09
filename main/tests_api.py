import uuid
from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser, Group, User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Comment, Experience, Projects
from main.permissions import (
    IsPortfolioOwnerOrEditorOrReadOnly,
    IsPortfolioOwnerOrReadOnly,
)
from main.serializers import ExperienceSerializer, ProjectSerializer


class ProjectAPITestBase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.user = User.objects.create_user(username="visitor", password="test-password")
        self.editor = User.objects.create_user(username="editor", password="test-password")
        self.editor.groups.add(Group.objects.create(name="Editor"))
        self.project = Projects.objects.create(
            name="Portfolio",
            description="My website",
            type="personal",
            image="https://example.com/portfolio.jpg",
            tech_stack=["Django"],
        )
        self.list_url = reverse("api:project-list")
        self.detail_url = reverse("api:project-detail", args=[self.project.id])
        self.star_url = reverse("api:project-star", args=[self.project.id])
        self.payload = {
            "name": "New project",
            "description": "A useful app",
            "type": "team",
            "url": "https://example.com/",
            "image": "https://example.com/new.jpg",
            "tech_stack": ["Python", "Django"],
        }

    def snapshot(self):
        self.project.refresh_from_db()
        return (
            Projects.objects.count(),
            self.project.name,
            self.project.description,
            self.project.starred_by.count(),
        )


class ProjectReadTest(ProjectAPITestBase):
    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data[0]
        self.assertEqual(item["id"], str(self.project.id))
        self.assertEqual(item["type_display"], "Personal")
        self.assertEqual(item["tech_stack"], ["Django"])
        self.assertFalse(item["is_starred"])
        self.assertNotIn("fields", item)
        self.assertNotIn("starred_by", item)

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Portfolio")

    def test_head_requests(self):
        self.assertEqual(self.client.head(self.list_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.head(self.detail_url).status_code, status.HTTP_200_OK)

    def test_search_by_name_and_type(self):
        Projects.objects.create(
            name="Contest Bot", description="Bot", type="competition",
            image="https://example.com/bot.jpg",
        )
        response = self.client.get(self.list_url, {"name": "PORT"})
        self.assertEqual([p["name"] for p in response.data], ["Portfolio"])
        response = self.client.get(self.list_url, {"type": "competition"})
        self.assertEqual([p["name"] for p in response.data], ["Contest Bot"])
        response = self.client.get(self.list_url, {"name": "not-found"})
        self.assertEqual(response.data, [])

    def test_missing_project(self):
        url = reverse("api:project-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        star_url = reverse("api:project-star", args=[uuid.uuid4()])
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.post(star_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_safe_methods_do_not_change_data(self):
        before = self.snapshot()
        for user in (None, self.user, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            for url in (self.list_url, self.detail_url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
                self.assertEqual(self.client.options(url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.snapshot(), before)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(
            self.client.delete(self.list_url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.get(self.star_url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class ProjectRolePermissionTest(ProjectAPITestBase):
    """Visitor reads; user reads + stars; Editor also PUT/PATCH; owner everything."""

    def assert_write_forbidden(self, user, expected_status):
        self.client.force_authenticate(user=user)
        before = self.snapshot()
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            expected_status,
        )
        self.assertEqual(
            self.client.patch(self.detail_url, {"name": "Changed"}, format="json").status_code,
            expected_status,
        )
        self.assertEqual(
            self.client.put(self.detail_url, self.payload, format="json").status_code,
            expected_status,
        )
        self.assertEqual(self.client.delete(self.detail_url).status_code, expected_status)
        self.assertEqual(self.snapshot(), before)

    def test_visitor_can_only_read(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_200_OK)
        self.assert_write_forbidden(None, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_regular_user_can_read_and_star_but_not_write(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
        self.assert_write_forbidden(self.user, status.HTTP_403_FORBIDDEN)

    def test_staff_without_editor_group_cannot_write(self):
        self.user.is_staff = True
        self.user.save()
        self.assert_write_forbidden(self.user, status.HTTP_403_FORBIDDEN)

    def test_editor_can_patch_and_put(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"name": "Edited"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Edited")
        self.assertEqual(self.project.description, "My website")

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "New project")
        self.assertEqual(self.project.tech_stack, ["Python", "Django"])

    def test_editor_can_patch_but_is_rejected_on_create_and_delete(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"name": "Edited"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Projects.objects.filter(name="New project").exists())

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Projects.objects.filter(pk=self.project.pk).exists())

    def test_editor_can_star(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["star_count"], 1)

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Projects.objects.filter(pk=response.data["id"]).exists())

        response = self.client.patch(self.detail_url, {"name": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, "My website")

        response = self.client.put(self.detail_url, {"name": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Projects.objects.filter(pk=self.project.id).exists())


class ProjectValidationTest(ProjectAPITestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.owner)

    def test_invalid_payloads_are_rejected(self):
        for changes, field in [
            ({"name": "   "}, "name"),
            ({"name": '<img src="x" onerror="alert(1)">'}, "name"),
            ({"name": "x" * 51}, "name"),
            ({"description": "<b></b>"}, "description"),
            ({"url": "javascript:alert(1)"}, "url"),
            ({"image": ""}, "image"),
            ({"type": "unknown"}, "type"),
            ({"tech_stack": "Django"}, "tech_stack"),
        ]:
            with self.subTest(field=field, changes=changes):
                response = self.client.post(
                    self.list_url, {**self.payload, **changes}, format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
        self.assertEqual(Projects.objects.count(), 1)

    def test_html_is_stripped_from_text_fields(self):
        response = self.client.post(self.list_url, {
            **self.payload,
            "name": "<b>Bold</b> name",
            "description": "<script>x</script>Desc",
            "tech_stack": ["<i>Python</i>", "  ", "<b></b>"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Bold name")
        self.assertEqual(response.data["description"], "xDesc")
        self.assertEqual(response.data["tech_stack"], ["Python"])

    def test_optional_fields_can_be_omitted(self):
        payload = {k: v for k, v in self.payload.items() if k not in ("url", "tech_stack")}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["url"])
        self.assertEqual(response.data["tech_stack"], [])

    def test_computed_fields_are_read_only(self):
        response = self.client.post(self.list_url, {
            **self.payload, "id": str(uuid.uuid4()), "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.user.id],
            "type_display": "Forged",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "")
        self.assertEqual(response.data["type_display"], "Team")
        project = Projects.objects.get(pk=response.data["id"])
        self.assertEqual(project.starred_by.count(), 0)


class ProjectStarTest(ProjectAPITestBase):
    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        self.assertEqual(response.data["starred_by_names"], "visitor")

        response = self.client.get(self.list_url)
        self.assertTrue(response.data[0]["is_starred"])

        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_is_starred_is_per_user(self):
        self.project.starred_by.add(self.owner)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)

    def test_serializer_without_request_context(self):
        data = ProjectSerializer(self.project).data
        self.assertFalse(data["is_starred"])


class CsrfTest(ProjectAPITestBase):
    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Projects.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PermissionClassTest(APITestCase):
    """Unit tests for the permission classes themselves."""

    def setUp(self):
        self.owner = User.objects.create_superuser(username="owner", password="pw")
        self.user = User.objects.create_user(username="user", password="pw")
        self.editor = User.objects.create_user(username="editor", password="pw")
        self.editor.groups.add(Group.objects.create(name="Editor"))

    def check(self, permission, method, user):
        request = SimpleNamespace(method=method, user=user)
        return permission.has_permission(request, view=None)

    def test_owner_or_read_only(self):
        permission = IsPortfolioOwnerOrReadOnly()
        self.assertTrue(self.check(permission, "GET", AnonymousUser()))
        self.assertTrue(self.check(permission, "OPTIONS", self.user))
        self.assertFalse(self.check(permission, "POST", AnonymousUser()))
        self.assertFalse(self.check(permission, "PATCH", self.editor))
        self.assertTrue(self.check(permission, "DELETE", self.owner))

    def test_owner_or_editor_or_read_only(self):
        permission = IsPortfolioOwnerOrEditorOrReadOnly()
        expected = {
            "anonymous": {"GET": True, "HEAD": True, "OPTIONS": True, "POST": False,
                          "PUT": False, "PATCH": False, "DELETE": False},
            "user": {"GET": True, "HEAD": True, "OPTIONS": True, "POST": False,
                     "PUT": False, "PATCH": False, "DELETE": False},
            "editor": {"GET": True, "HEAD": True, "OPTIONS": True, "POST": False,
                       "PUT": True, "PATCH": True, "DELETE": False},
            "owner": {"GET": True, "HEAD": True, "OPTIONS": True, "POST": True,
                      "PUT": True, "PATCH": True, "DELETE": True},
        }
        users = {
            "anonymous": AnonymousUser(), "user": self.user,
            "editor": self.editor, "owner": self.owner,
        }
        for role, methods in expected.items():
            for method, allowed in methods.items():
                with self.subTest(role=role, method=method):
                    self.assertEqual(
                        self.check(permission, method, users[role]), allowed,
                    )

    def test_group_must_be_named_editor(self):
        other = User.objects.create_user(username="other", password="pw")
        other.groups.add(Group.objects.create(name="Editors"))
        permission = IsPortfolioOwnerOrEditorOrReadOnly()
        self.assertFalse(self.check(permission, "PATCH", other))


# ======================= Experience API ======================= #
class ExperienceAPITestBase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.user = User.objects.create_user(
            username="visitor", password="test-password", email="visitor@example.com",
        )
        self.editor = User.objects.create_user(username="editor", password="test-password")
        self.editor.groups.add(Group.objects.create(name="Editor"))
        self.experience = Experience.objects.create(
            title="Teaching Assistant",
            description="Helped students.",
            category="part-time",
        )
        self.list_url = reverse("api:experience-list")
        self.detail_url = reverse("api:experience-detail", args=[self.experience.id])
        self.star_url = reverse("api:experience-star", args=[self.experience.id])
        self.comment_url = reverse("api:experience-comment-list", args=[self.experience.id])
        self.payload = {
            "title": "Backend Intern",
            "description": "Built REST APIs.",
            "category": "internship",
            "thumbnail": "https://example.com/intern.jpg",
            "started_at": "2025-01-01",
            "ended_at": "2025-06-30",
        }

    def snapshot(self):
        self.experience.refresh_from_db()
        return (
            Experience.objects.count(),
            self.experience.title,
            self.experience.description,
            self.experience.starred_by.count(),
        )


class ExperienceReadTest(ExperienceAPITestBase):
    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data[0]
        self.assertEqual(item["id"], str(self.experience.id))
        self.assertEqual(item["category"], "part-time")
        self.assertEqual(item["category_display"], "Part-Time")
        self.assertTrue(item["is_ongoing"])
        self.assertEqual(item["star_count"], 0)
        self.assertFalse(item["is_starred"])
        self.assertEqual(item["comments"], [])
        self.assertIsNone(item["user_comment"])

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Teaching Assistant")
        self.assertEqual(self.client.head(self.list_url).status_code, status.HTTP_200_OK)

    def test_explicit_fields_and_no_sensitive_account_data(self):
        self.experience.starred_by.add(self.user)
        Comment.objects.create(experience=self.experience, commented_by=self.user, text="Nice")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(set(response.data), {
            "id", "title", "description", "category", "category_display", "thumbnail",
            "started_at", "ended_at", "is_ongoing", "star_count", "is_starred",
            "starred_by_names", "comments", "user_comment",
        })
        self.assertEqual(response.data["starred_by_names"], "visitor")
        self.assertEqual(
            set(response.data["comments"][0]), {"id", "text", "username", "created_at"},
        )
        content = response.content.decode()
        for secret in ("visitor@example.com", "password", "owner@example.com"):
            self.assertNotIn(secret, content)

    def test_search_by_title_and_category(self):
        Experience.objects.create(title="Hackathon", description="Won.", category="research")
        response = self.client.get(self.list_url, {"search": "TEACH"})
        self.assertEqual([e["title"] for e in response.data], ["Teaching Assistant"])
        response = self.client.get(self.list_url, {"category": "research"})
        self.assertEqual([e["title"] for e in response.data], ["Hackathon"])
        response = self.client.get(self.list_url, {"search": "Hack", "category": "part-time"})
        self.assertEqual(response.data, [])

    def test_missing_experience_returns_404(self):
        missing = uuid.uuid4()
        self.client.force_authenticate(user=self.owner)
        detail = reverse("api:experience-detail", args=[missing])
        comments = reverse("api:experience-comment-list", args=[missing])
        star = reverse("api:experience-star", args=[missing])
        self.assertEqual(self.client.get(detail).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(comments).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(star).status_code, status.HTTP_404_NOT_FOUND)

    def test_wrong_methods(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(
            self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.get(self.star_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_list_query_count_is_constant(self):
        def count_queries():
            with CaptureQueriesContext(connection) as ctx:
                self.assertEqual(self.client.get(self.list_url).status_code, 200)
            return len(ctx)

        self.client.force_authenticate(user=self.user)
        baseline = count_queries()
        for index in range(5):
            experience = Experience.objects.create(title=f"E{index}", description="d")
            experience.starred_by.add(self.user, self.owner)
            Comment.objects.create(experience=experience, commented_by=self.owner, text="hi")
        self.assertEqual(count_queries(), baseline)


class ExperienceRolePermissionTest(ExperienceAPITestBase):
    def assert_write_forbidden(self, user):
        self.client.force_authenticate(user=user)
        before = self.snapshot()
        forbidden = status.HTTP_403_FORBIDDEN
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, forbidden)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, forbidden)
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, forbidden)
        self.assertEqual(self.client.delete(self.detail_url).status_code, forbidden)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(Experience.objects.filter(title="Backend Intern").exists())

    def test_visitor_is_rejected_on_write(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_200_OK)
        self.assert_write_forbidden(None)

    def test_regular_user_is_rejected_on_write(self):
        self.assert_write_forbidden(self.user)

    def test_staff_without_editor_group_is_rejected(self):
        self.user.is_staff = True
        self.user.save()
        self.assert_write_forbidden(self.user)

    def test_editor_can_patch_and_put(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"title": "Edited"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Edited")
        self.assertEqual(self.experience.description, "Helped students.")

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Backend Intern")
        self.assertEqual(self.experience.category, "internship")

    def test_editor_is_rejected_on_create_and_delete(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Experience.objects.filter(title="Backend Intern").exists())

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Experience.objects.get(pk=response.data["id"])
        self.assertEqual(created.title, "Backend Intern")
        self.assertEqual(created.ended_at.date().isoformat(), "2025-06-30")

        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.description, "Helped students.")

        response = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Experience.objects.filter(pk=self.experience.pk).exists())


class ExperienceValidationTest(ExperienceAPITestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.owner)

    def test_invalid_payloads_are_rejected(self):
        for changes, field in [
            ({"title": "   "}, "title"),
            ({"title": '<img src="x" onerror="alert(1)">'}, "title"),
            ({"title": "x" * 256}, "title"),
            ({"description": "<b></b>"}, "description"),
            ({"category": "unknown"}, "category"),
            ({"thumbnail": "javascript:alert(1)"}, "thumbnail"),
            ({"started_at": "not-a-date"}, "started_at"),
            ({"ended_at": "2024-12-31"}, "ended_at"),
        ]:
            with self.subTest(field=field, changes=changes):
                response = self.client.post(
                    self.list_url, {**self.payload, **changes}, format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
        self.assertEqual(Experience.objects.count(), 1)

    def test_partial_update_validates_dates_against_stored_value(self):
        self.experience.started_at = timezone.now() - timedelta(days=10)
        self.experience.save()
        before = self.snapshot()
        end = (timezone.now() - timedelta(days=20)).date().isoformat()
        response = self.client.patch(self.detail_url, {"ended_at": end}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ended_at", response.data)
        self.assertEqual(self.snapshot(), before)
        self.experience.refresh_from_db()
        self.assertIsNone(self.experience.ended_at)

    def test_html_is_stripped_from_text_fields(self):
        response = self.client.post(self.list_url, {
            **self.payload,
            "title": "<b>Bold</b> title",
            "description": "<script>x</script>Desc",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Bold title")
        self.assertEqual(response.data["description"], "xDesc")

    def test_optional_fields_can_be_omitted_and_cleared(self):
        payload = {"title": "Minimal", "description": "Only required."}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["ended_at"])
        self.assertEqual(response.data["category"], "freelance")

        url = reverse("api:experience-detail", args=[response.data["id"]])
        self.client.patch(url, {"ended_at": "2030-01-01"}, format="json")
        response = self.client.patch(url, {"ended_at": None, "thumbnail": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["ended_at"])

    def test_computed_fields_are_read_only(self):
        response = self.client.post(self.list_url, {
            **self.payload, "id": str(uuid.uuid4()), "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "is_ongoing": True, "comments": [{"text": "x"}],
            "category_display": "Forged",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "")
        self.assertFalse(response.data["is_ongoing"])
        self.assertEqual(response.data["comments"], [])
        self.assertEqual(response.data["category_display"], "Internship")
        self.assertEqual(Comment.objects.count(), 0)


class ExperienceStarTest(ExperienceAPITestBase):
    def test_visitor_cannot_star(self):
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_star_toggles_for_logged_in_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        self.assertEqual(response.data["starred_by_names"], "visitor")
        self.assertTrue(self.client.get(self.list_url).data[0]["is_starred"])

        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_star_account_comes_from_request_user_only(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            self.star_url, {"user": self.owner.id, "starred_by": [self.owner.id]}, format="json",
        )
        self.assertEqual(list(self.experience.starred_by.all()), [self.user])

    def test_is_starred_is_per_user(self):
        self.experience.starred_by.add(self.owner)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)

    def test_serializer_without_request_context(self):
        data = ExperienceSerializer(self.experience).data
        self.assertFalse(data["is_starred"])
        self.assertIsNone(data["user_comment"])


class ExperienceCommentAPITest(ExperienceAPITestBase):
    def test_visitor_can_read_but_not_comment(self):
        Comment.objects.create(experience=self.experience, commented_by=self.user, text="Nice")
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["username"], "visitor")

        response = self.client.post(self.comment_url, {"text": "Hi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_is_created_then_updated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.comment_url, {"text": "First"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(self.comment_url, {"text": "<b>Second</b>"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, "Second")
        self.assertEqual(comment.commented_by, self.user)

        item = self.client.get(self.detail_url).data
        self.assertEqual(item["user_comment"]["text"], "Second")
        self.assertEqual(len(item["comments"]), 1)

    def test_comment_author_and_target_cannot_be_forged(self):
        other = Experience.objects.create(title="Other", description="d")
        self.client.force_authenticate(user=self.user)
        self.client.post(self.comment_url, {
            "text": "Mine", "commented_by": self.owner.id, "experience": str(other.id),
        }, format="json")
        comment = Comment.objects.get()
        self.assertEqual(comment.commented_by, self.user)
        self.assertEqual(comment.experience, self.experience)

    def test_invalid_comment_is_rejected(self):
        self.client.force_authenticate(user=self.user)
        for text in ("   ", "<i></i>", "x" * 101):
            with self.subTest(text=text):
                response = self.client.post(self.comment_url, {"text": text}, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 0)


class ExperienceCsrfTest(ExperienceAPITestBase):
    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Experience.objects.count(), 1)
        self.assertEqual(client.delete(self.detail_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        client.get(self.list_url, HTTP_ACCEPT="text/html")
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ExperiencePageTest(ExperienceAPITestBase):
    def test_page_is_wired_to_the_api_and_sets_csrf_cookie(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, self.list_url)
        self.assertContains(response, 'id="edit-experience-modal"')
        self.assertContains(response, 'id="add-experience-modal"')
        self.assertIn("csrftoken", response.cookies)

    def test_modals_follow_roles(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, 'id="edit-experience-modal"')
        self.assertNotContains(response, 'id="add-experience-modal"')

        self.client.force_login(self.user)
        response = self.client.get(reverse("main:show_experience"))
        self.assertNotContains(response, 'id="edit-experience-modal"')
