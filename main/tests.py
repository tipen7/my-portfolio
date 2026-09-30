from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.forms import ProjectForm
from main.models import Comment, Experience, Projects


class MainTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner",
            password="owner-password",
        )
        self.client.login(username="owner", password="owner-password")
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

        Comment.objects.create(
            experience=self.experience,
            commented_by=self.owner,
            text="A useful experience.",
        )
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, "experience-comments-trigger")
        self.assertContains(response, "experience-comment__avatar")
        self.assertContains(response, "Sent")

    def test_authenticated_user_can_create_and_update_one_experience_comment(self):
        response = self.client.post(
            reverse("main:comment_experience", args=[self.experience.id]),
            {"text": "First comment"},
        )
        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertEqual(
            Comment.objects.filter(
                experience=self.experience,
                commented_by=self.owner,
            ).count(),
            1,
        )

        self.client.post(
            reverse("main:comment_experience", args=[self.experience.id]),
            {"text": "Updated comment"},
        )
        comment = Comment.objects.get(
            experience=self.experience,
            commented_by=self.owner,
        )
        self.assertEqual(comment.text, "Updated comment")
        self.assertEqual(
            Comment.objects.filter(
                experience=self.experience,
                commented_by=self.owner,
            ).count(),
            1,
        )

    def test_anonymous_user_cannot_comment_on_experience(self):
        self.client.logout()

        response = self.client.post(
            reverse("main:comment_experience", args=[self.experience.id]),
            {"text": "Anonymous comment"},
        )

        self.assertRedirects(
            response,
            f'{reverse("main:login")}?next={reverse("main:comment_experience", args=[self.experience.id])}',
            fetch_redirect_response=False,
        )
        self.assertFalse(Comment.objects.exists())

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")

    def test_future_end_date_keeps_experience_ongoing(self):
        self.experience.ended_at = timezone.now() + timezone.timedelta(days=30)
        self.experience.save()

        response = self.client.get(reverse("main:show_experience"))

        self.assertTrue(self.experience.is_ongoing)
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, "sekarang")
        self.assertNotContains(response, "None")

    def test_experience_form_rejects_end_date_before_start_date(self):
        response = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "Invalid Timeline",
                "description": "This timeline is invalid.",
                "category": "research",
                "thumbnail": "",
                "started_at": "2026-09-19",
                "ended_at": "2026-09-18",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "End date must be on or after the start date.")

    def test_experience_can_be_created_with_form(self):
        response = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "Backend Intern",
                "description": "Built internal services.",
                "category": "internship",
                "thumbnail": "https://example.com/internship.jpg",
            },
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertTrue(Experience.objects.filter(title="Backend Intern").exists())

    def test_experience_can_be_updated_with_form(self):
        response = self.client.post(
            reverse("main:update_experience", args=[self.experience.id]),
            {
                "title": "Updated Teaching Assistant",
                "description": "Updated description.",
                "category": "research",
                "thumbnail": "",
            },
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Updated Teaching Assistant")
        self.assertEqual(self.experience.category, "research")

    def test_experience_can_be_deleted(self):
        response = self.client.post(
            reverse("main:delete_experience", args=[self.experience.id])
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertFalse(Experience.objects.filter(id=self.experience.id).exists())

    def test_experience_json_delivery_and_category_filter(self):
        response = self.client.get(
            reverse("main:get_experiences_json"),
            {"category": "part-time"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertContains(response, self.experience.title)

        filtered_response = self.client.get(
            reverse("main:show_experience"),
            {"category": "internship"},
        )
        self.assertNotContains(filtered_response, self.experience.title)

    def test_project_page_displays_saved_project(self):
        project = Projects.objects.create(
            name="Django Portfolio",
            description="A portfolio project.",
            type="personal",
            image="https://example.com/project.jpg",
            tech_stack=["Django", "Next.js"],
        )

        response = self.client.get(reverse("main:show_projects"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.name)
        self.assertContains(response, "Django")
        self.assertContains(response, "Next.js")
        self.assertContains(response, "Hapus Proyek")
        self.assertContains(response, f"Hapus {project.name}")

        api_response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(api_response.status_code, 200)
        self.assertContains(api_response, project.name)
        self.assertNotContains(api_response, "starred_by")

    def test_project_search_uses_project_name(self):
        Projects.objects.create(
            name="Django Portfolio",
            description="A portfolio project.",
            type="personal",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(
            reverse("main:show_projects"),
            {"title": "Django"},
        )

        self.assertContains(response, "Django Portfolio")

    def test_project_can_be_updated_with_form(self):
        project = Projects.objects.create(
            name="Django Portfolio",
            description="A portfolio project.",
            type="personal",
            image="https://example.com/project.jpg",
            tech_stack=["Django", "Python"],
        )

        response = self.client.post(
            reverse("main:update_project", args=[project.id]),
            {
                "name": "Updated Portfolio",
                "description": "An updated portfolio project.",
                "type": "team",
                "url": "https://example.com/updated",
                "image": "https://example.com/updated.jpg",
                "tech_stack": "Django, Python, PostgreSQL",
            },
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Portfolio")
        self.assertEqual(project.type, "team")
        self.assertEqual(project.tech_stack, ["Django", "Python", "PostgreSQL"])

    def test_project_form_does_not_expose_starred_by(self):
        self.assertNotIn("starred_by", ProjectForm().fields)

    def test_project_name_is_escaped_in_public_html_and_json(self):
        payload = "<img src=\"x\" onerror=\"alert('XSS!')\">"
        project = Projects.objects.create(
            name=payload,
            description="A project with a text-only name.",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(response, payload, html=False)
        self.assertNotContains(response, payload, html=True)
        self.assertContains(response, "&lt;img", html=False)

        api_response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(api_response.json()[0]["fields"]["name"], payload)
        self.assertEqual(str(project.id), api_response.json()[0]["pk"])

    def test_project_name_with_attribute_breakout_is_not_rendered_as_html(self):
        payload = '\"><img src=x onerror=\"alert(1)\">'
        Projects.objects.create(
            name=payload,
            description="A project with an attribute breakout attempt.",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(response, '<img src=x onerror="alert(1)">', html=True)
        self.assertContains(response, "&quot;&gt;&lt;img", html=False)

    def test_ajax_project_creation_keeps_name_as_text(self):
        payload = '<img src="x" onerror="alert(\'XSS!\')">'
        response = self.client.post(
            reverse("main:create_project_ajax"),
            {
                "name": payload,
                "description": "Created through the project modal.",
                "type": "personal",
                "image": "https://example.com/project.jpg",
                "tech_stack": "Django, Python",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Projects.objects.filter(name=payload).exists())
        self.assertNotContains(
            self.client.get(reverse("main:show_projects")),
            payload,
            html=True,
        )

    def test_project_card_has_edit_and_delete_actions(self):
        project = Projects.objects.create(
            name="Django Portfolio",
            description="A portfolio project.",
            type="personal",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(
            response,
            f'href="{reverse("main:update_project", args=[project.id])}"',
        )
        self.assertContains(response, "Hapus Proyek")

    def test_anonymous_user_can_read_but_cannot_change_portfolio(self):
        self.client.logout()
        project = Projects.objects.create(
            name="Public Project",
            description="Visible to everyone.",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(reverse("main:show_projects"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("main:update_project", args=[project.id]),
        )
        self.assertNotContains(response, "Hapus Proyek")
        self.assertRedirects(
            self.client.post(reverse("main:toggle_star", args=[project.id])),
            f'{reverse("main:login")}?next={reverse("main:toggle_star", args=[project.id])}',
            fetch_redirect_response=False,
        )

    def test_regular_user_can_toggle_star_but_cannot_edit(self):
        user = User.objects.create_user(username="visitor", password="password")
        project = Projects.objects.create(
            name="Starred Project",
            description="A project to star.",
            image="https://example.com/project.jpg",
        )
        self.client.login(username="visitor", password="password")

        self.client.post(reverse("main:toggle_star", args=[project.id]))
        self.assertTrue(project.starred_by.filter(pk=user.pk).exists())
        self.client.post(reverse("main:toggle_star", args=[project.id]))
        self.assertFalse(project.starred_by.filter(pk=user.pk).exists())
        self.assertEqual(
            self.client.post(
                reverse("main:update_project", args=[project.id]),
                {},
            ).status_code,
            403,
        )

    def test_editor_can_update_but_cannot_create_or_delete(self):
        editor = User.objects.create_user(username="editor", password="password")
        editor.groups.add(Group.objects.create(name="Editor"))
        project = Projects.objects.create(
            name="Editable Project",
            description="An editable project.",
            image="https://example.com/project.jpg",
        )
        self.client.login(username="editor", password="password")

        response = self.client.post(
            reverse("main:update_project", args=[project.id]),
            {
                "name": "Updated by Editor",
                "description": "Updated description.",
                "type": "personal",
                "url": "",
                "image": "https://example.com/updated.jpg",
                "tech_stack": "Django",
            },
        )
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertEqual(
            self.client.post(
                reverse("main:create_project"),
                {
                    "name": "Forbidden Project",
                    "description": "Should not be created.",
                    "type": "personal",
                    "image": "https://example.com/forbidden.jpg",
                },
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("main:delete_project", args=[project.id]),
            ).status_code,
            403,
        )