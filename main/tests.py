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
        self.assertContains(response, reverse("api:experience-list"))
        self.assertContains(response, f'href="{reverse("main:show_main")}"')
        self.assertTrue(response.context["can_edit"])
        self.assertTrue(response.context["can_manage"])

        Comment.objects.create(
            experience=self.experience,
            commented_by=self.owner,
            text="A useful experience.",
        )
        fields = self.client.get(reverse("main:get_experiences_json")).json()[0]["fields"]
        self.assertEqual(fields["title"], self.experience.title)
        self.assertEqual(fields["description"], self.experience.description)
        self.assertEqual(fields["category_display"], "Part-Time")
        self.assertTrue(fields["is_ongoing"])
        self.assertIsNone(fields["ended_at"])
        self.assertEqual(fields["comments"][0]["username"], "owner")
        self.assertEqual(fields["user_comment"]["text"], "A useful experience.")

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

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan")
        self.assertEqual(self.client.get(reverse("main:get_experiences_json")).json(), [])

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        fields = self.client.get(reverse("main:get_experiences_json")).json()[0]["fields"]

        self.assertFalse(self.experience.is_ongoing)
        self.assertFalse(fields["is_ongoing"])
        self.assertEqual(fields["ended_at"], self.experience.ended_at.isoformat())

    def test_future_end_date_keeps_experience_ongoing(self):
        self.experience.ended_at = timezone.now() + timezone.timedelta(days=30)
        self.experience.save()

        fields = self.client.get(reverse("main:get_experiences_json")).json()[0]["fields"]

        self.assertTrue(self.experience.is_ongoing)
        self.assertTrue(fields["is_ongoing"])

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
            reverse("main:get_experiences_json"),
            {"category": "internship"},
        )
        self.assertEqual(filtered_response.json(), [])

        search_response = self.client.get(
            reverse("main:get_experiences_json"),
            {"search": "asisten"},
        )
        self.assertEqual(len(search_response.json()), 1)
        self.assertEqual(
            self.client.get(reverse("main:get_experiences_json"), {"search": "zzz"}).json(),
            [],
        )

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
        self.assertTemplateUsed(response, "projects.html")
        self.assertContains(response, reverse("api:project-list"))
        self.assertContains(response, 'id="add-project-modal"')

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
        self.assertContains(response, 'value="Django"')

        json_response = self.client.get(
            reverse("main:get_projects_json"),
            {"title": "django", "type": "personal"},
        )
        self.assertEqual(json_response.json()[0]["fields"]["name"], "Django Portfolio")
        self.assertEqual(
            self.client.get(reverse("main:get_projects_json"), {"type": "team"}).json(),
            [],
        )

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

    def test_project_form_prefills_tech_stack_only_when_editing(self):
        self.assertNotIn("tech_stack", ProjectForm().initial)
        project = Projects.objects.create(
            name="Saved", description="Desc", image="https://example.com/p.jpg",
            tech_stack=["Django", "Python"],
        )
        self.assertEqual(
            ProjectForm(instance=project).initial["tech_stack"], "Django, Python",
        )

    def test_project_name_is_escaped_in_public_html_and_json(self):
        payload = "<img src=\"x\" onerror=\"alert('XSS!')\">"
        project = Projects.objects.create(
            name=payload,
            description="A project with a text-only name.",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(response, payload, html=False)

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
        self.assertNotContains(response, payload, html=False)
        api_response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(api_response.json()[0]["fields"]["name"], payload)

    def test_ajax_project_creation_strips_html(self):
        data = {
            "name": '<b>Safe</b> <img src="x" onerror="alert(1)">Name',
            "description": "Created through the project modal.",
            "type": "personal",
            "image": "https://example.com/project.jpg",
            "tech_stack": "Django, <i>Python</i>, ,",
        }
        response = self.client.post(
            reverse("main:create_project_ajax"),
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 201)
        project = Projects.objects.get(pk=response.json()["pk"])
        self.assertEqual(project.name, "Safe Name")
        self.assertEqual(project.tech_stack, ["Django", "Python"])

        response = self.client.post(
            reverse("main:create_project_ajax"),
            {**data, "name": '<img src="x">'},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json()["errors"])

    def test_project_card_has_edit_and_delete_actions(self):
        project = Projects.objects.create(
            name="Django Portfolio",
            description="A portfolio project.",
            type="personal",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(reverse("main:show_projects"))

        self.assertTrue(response.context["can_edit"])
        self.assertTrue(response.context["can_manage"])
        edit_response = self.client.get(reverse("main:update_project", args=[project.id]))
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, project.name)

    def test_anonymous_user_can_read_but_cannot_change_portfolio(self):
        self.client.logout()
        project = Projects.objects.create(
            name="Public Project",
            description="Visible to everyone.",
            image="https://example.com/project.jpg",
        )

        response = self.client.get(reverse("main:show_projects"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_edit"])
        self.assertFalse(response.context["can_manage"])
        self.assertNotContains(response, 'id="add-project-modal"')
        self.assertFalse(
            self.client.get(reverse("main:get_projects_json")).json()[0]["fields"]["is_starred"]
        )
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


class AuthViewsTest(TestCase):
    def test_register_get_and_post(self):
        response = self.client.get(reverse("main:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")

        response = self.client.post(reverse("main:register"), {
            "username": "newuser",
            "password1": "Str0ng-Passw0rd!",
            "password2": "Str0ng-Passw0rd!",
        })
        self.assertRedirects(response, reverse("main:login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_logout(self):
        User.objects.create_user(username="someone", password="pw-12345")
        response = self.client.get(reverse("main:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

        response = self.client.post(
            reverse("main:login"), {"username": "someone", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.post(
            reverse("main:login"), {"username": "someone", "password": "pw-12345"},
        )
        self.assertRedirects(response, reverse("main:show_main"))
        self.assertIn("last_login", response.cookies)
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.get(reverse("main:logout"))
        self.assertRedirects(response, reverse("main:show_main"))
        self.assertNotIn("_auth_user_id", self.client.session)


class RolePermissionViewsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(username="owner", password="pw")
        self.user = User.objects.create_user(username="user", password="pw")
        self.editor = User.objects.create_user(username="editor", password="pw")
        self.editor.groups.add(Group.objects.create(name="Editor"))
        self.experience = Experience.objects.create(
            title="Asisten Dosen", description="Desc", category="part-time",
        )
        self.project = Projects.objects.create(
            name="Project", description="Desc", image="https://example.com/p.jpg",
        )
        self.project_data = {
            "name": "Created Project",
            "description": "Created description.",
            "type": "team",
            "url": "",
            "image": "https://example.com/new.jpg",
            "tech_stack": "",
        }
        self.experience_data = {
            "title": "Created Experience",
            "description": "Created description.",
            "category": "research",
            "thumbnail": "",
            "started_at": "2026-01-01",
            "ended_at": "",
        }

    def test_comment_str(self):
        comment = Comment.objects.create(
            experience=self.experience, commented_by=self.user, text="Nice",
        )
        self.assertEqual(str(comment), "Comment by user on Asisten Dosen")

    def test_ajax_create_requires_owner(self):
        for user in (None, self.user, self.editor):
            if user:
                self.client.force_login(user)
            else:
                self.client.logout()
            response = self.client.post(reverse("main:create_project_ajax"), self.project_data)
            self.assertEqual(response.status_code, 403)
            response = self.client.post(reverse("main:create_experience_ajax"), self.experience_data)
            self.assertEqual(response.status_code, 403)
        self.assertFalse(Projects.objects.filter(name="Created Project").exists())
        self.assertFalse(Experience.objects.filter(title="Created Experience").exists())

    def test_owner_ajax_create_experience(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("main:create_experience_ajax"), self.experience_data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Experience.objects.filter(pk=response.json()["pk"]).exists())

        response = self.client.post(
            reverse("main:create_experience_ajax"), {**self.experience_data, "title": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["errors"])

    def test_owner_ajax_create_project_with_empty_tech_stack(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("main:create_project_ajax"), self.project_data)
        self.assertEqual(response.status_code, 201)
        project = Projects.objects.get(pk=response.json()["pk"])
        self.assertEqual(project.tech_stack, [])

    def test_ajax_endpoints_require_post(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("main:create_project_ajax")).status_code, 405)
        self.assertEqual(self.client.get(reverse("main:create_experience_ajax")).status_code, 405)

    def test_owner_create_project_form(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("main:create_project"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")

        response = self.client.post(reverse("main:create_project"), self.project_data)
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(Projects.objects.filter(name="Created Project").exists())

    def test_owner_can_delete_project(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("main:delete_project", args=[self.project.id]))
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(Projects.objects.filter(pk=self.project.pk).exists())

    def test_experience_form_pages(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("main:create_experience"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_editing"])

        response = self.client.get(reverse("main:update_experience", args=[self.experience.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_editing"])

    def test_editor_can_update_experience_but_not_create_or_delete(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("main:update_experience", args=[self.experience.id]),
            {**self.experience_data, "title": "Edited by Editor"},
        )
        self.assertRedirects(response, reverse("main:show_experience"))
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Edited by Editor")

        self.assertEqual(self.client.get(reverse("main:create_experience")).status_code, 403)
        self.assertEqual(
            self.client.post(reverse("main:delete_experience", args=[self.experience.id])).status_code,
            403,
        )
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())

    def test_regular_user_cannot_update_experience(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("main:update_experience", args=[self.experience.id]))
        self.assertEqual(response.status_code, 403)

    def test_invalid_comment_shows_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("main:comment_experience", args=[self.experience.id]),
            {"text": "x" * 101},
            follow=True,
        )
        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertIn(
            "Please enter a comment of 100 characters or fewer.",
            [str(message) for message in response.context["messages"]],
        )
        self.assertFalse(Comment.objects.exists())

    def test_comment_ajax_create_update_and_validate(self):
        url = reverse("main:comment_experience_ajax", args=[self.experience.id])
        self.client.force_login(self.user)

        response = self.client.post(url, {"text": "First"})
        self.assertEqual(response.status_code, 201)
        comment_pk = response.json()["pk"]

        response = self.client.post(url, {"text": "<b>Updated</b>"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["pk"], comment_pk)
        self.assertEqual(Comment.objects.get(pk=comment_pk).text, "Updated")

        response = self.client.post(url, {"text": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("text", response.json()["errors"])
        self.assertEqual(Comment.objects.count(), 1)

        missing = reverse(
            "main:comment_experience_ajax", args=["00000000-0000-0000-0000-000000000000"],
        )
        self.assertEqual(self.client.post(missing, {"text": "x"}).status_code, 404)

    def test_projects_json_is_starred_for_logged_in_user(self):
        self.project.starred_by.add(self.user)
        self.client.force_login(self.user)
        fields = self.client.get(reverse("main:get_projects_json")).json()[0]["fields"]
        self.assertTrue(fields["is_starred"])
        self.assertEqual(fields["star_count"], 1)