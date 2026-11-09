# My Portfolio Project

---

## 👤 Author Information

| Field     | Details                |
| :-------- | :--------------------- |
| **Name**  | Steven Dyanizha Ananda |
| **NPM**   | 2506616112             |
| **Class** | A                      |

---

## 🚀 Progress Update


- [x] Created APIs using DRF
- [x] Implemented REST API's for other models in the main app (views, models, serializers, api_views, etc.)
- [x] Rebuilded and refactored design system tokens and components


### Tugas 6

1. **REST** (Representational State Transfer) is a set of design rules for web APIs. The main ideas are:
- Everything is a **resource** with its own URL, like `/api/experiences/1/`.
- You use **HTTP methods** for actions: GET to read, POST to create, PUT/PATCH to update, DELETE to delete.
- The server is **stateless**. Each request carries everything the server needs, and the server doesn't remember earlier requests.
- The server returns proper **HTTP status codes**, like 200, 201, 400, 404.

Returning JSON isn't enough because JSON is only a data format. An API could return JSON from `/getExperience` and `/deleteExperience` using only POST and always answer `200 OK`. That is JSON over HTTP, but it ignores REST's rules. To be RESTful, the API also needs resource-based URLs, correct methods, and meaningful status codes.

**PUT vs PATCH:**
- **PUT** replaces the whole resource. You must send all the fields. Any field you leave out may be reset or rejected.
- **PATCH** updates only the fields you send. The rest will stay the same.

Here are cases when do we need to use **PATCH** and **PUT**
- Use **PATCH** when we only want to change one thing such as fixing a typo in an experience's `title`.
- Use **PUT** when we want to submit a full edited form and want to overwrite the whole record with the new data.



2. A **serializer** in DRF does two jobs:
a. It **converts** Django model objects into JSON-friendly data (serialization) and converts incoming JSON back into Python data (deserialization).
b.  It **validates** incoming data, e.g. required fields, max length, and types.

Advantages over building a dictionary by hand with `JsonResponse`:
- **Less repetitive code.** We declare the fields once instead of writing `{"id": obj.id, "title": obj.title, ...}` in every view.
- **Built-in validation.** It checks input and gives clear error messages. With manual dictionaries we would have to write all of that yourself.
- **Easier to maintain.** If we add a field to the model, we update the serializer in one place, not every view.
- **Handles relations and nested data**, like comments inside an experience, and `ModelSerializer` can create and update objects for us.
- **Fewer bugs.** Hand-built dictionaries make it easy to forget a field or leak one we shouldn't expose.

3. 
- **Authentication** asks "Who are you?" It checks your identity, for example with a session, token, or login.
- **Authorization** asks "What are you allowed to do?" It checks whether you may do this specific action such as deleting someone else's comment.

In DRF, authentication classes (like `SessionAuthentication`) identify the user. Permission classes (like `IsAuthenticated` or a custom `IsOwner`) decide whether the user can proceed.

Permissions must be checked on the server because hiding a button in a template is only a template. Anyone can:
- open the browser dev tools and show the hidden button,
- or skip the page and send the request directly with `curl`, Postman, or a script.

The server is the only place the user can't bypass. If it doesn't check permissions, anyone who knows the URL can change or delete data. Hiding buttons is good for UX, but the permission class is what provides security.


4. With `SessionAuthentication`, the browser **automatically sends the session cookie** on every request to your site. That is the problem. If you are logged in and visit a malicious site, that site can make your browser send a `POST` or `DELETE` to your API, and the cookie goes along with it. The server would think it is really you. This is a **CSRF** (Cross-Site Request Forgery) attack.

The **CSRF token** fixes this. A malicious site can't read your token, so it can't include the right one. Requests that change data (POST, PUT, PATCH, DELETE) must therefore send a valid token, and the server rejects the ones that don't.

`force_authenticate` isn't enough for a test because it **bypasses the real authentication process**. It tells DRF "pretend this user is logged in" and skips the `SessionAuthentication` class. Since DRF enforces the CSRF check inside `SessionAuthentication`, the check never runs. A test using `force_authenticate` can pass even if your CSRF protection is broken. To really test CSRF, you need to log in with a real session (like `client.login()`) and use a client with `enforce_csrf_checks=True`. Then you can check that a request without a token is rejected (403) and one with a valid token succeeds.


### AI Disclosure
I used Anthropic (Claude) AI to help me rebuild and redesign my entire frontend and user interface designs, this includes design system tokens, color and components. Even though I used AI, i always double check and ran test along to see the AI's result, and sometimes it is still not as i expected. 

For this new topic about DRF, I have an intermediate experince working with this framework, hence i wrote all the backend and server-side logic myself. For the testing, I also used AI to help me with writing boilerplate codes for me to write the logic myself. 


Reference: (Django REST Framework)[https://www.django-rest-framework.org/api-guide/views/]

---