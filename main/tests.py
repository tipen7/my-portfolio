from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Projects


class MainTest(TestCase):
    def setUp(self):
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