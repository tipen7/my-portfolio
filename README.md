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

- [x] Added new Form model for Experience (**ExperienceForm**) in `main/forms.py`
- [x] Altered Experience model and changing the `started_at` field to be editable
- [x] Registered a new routes for Experience CRUD operations  in `main/urls.py`
- [x] Created views for Experience CRUD Operations in `main/views.py`
- [x] Created Unit Tests spesifically for handling the Experience form in `main/tests.py`
- [x] Improved UI designs to be matched with design system tokes in `style.css`
- [x] Answered Tugas 3 Questions

---

### Tugas 3

1. `ModelForm` is used because the form can be generated from a Django model definition. This allows the fields, data types, basic validation, and database-saving process to be managed more consistently. In this project, `ExperienceForm` represents the `Experience` model, while `ProjectForm` represents the `Projects` model.

If I created the HTML forms manually, I would have to write every input, configure validation, retrieve data from `request.POST`, and map that data to a model object myself. The manual approach can still be useful for specific requirements, but it is more likely to cause duplication or inconsistencies between the form and the model. `ModelForm` reduces this work because Django can generate form fields from the model and display validation errors on the appropriate fields.

`ModelForm` can also be customized. For example, in `ExperienceForm`, I configured the date widget as `input type="date"` and added validation to ensure that `ended_at` cannot be earlier or less than the `started_at` field.

The `{% csrf_token %}` tag must be added to forms that send requests such as `POST`, especially for create, update, and delete operations. This tag generates a security token associated with the user's session or cookie. Django checks the token before processing the request.

Its purpose is to prevent **Cross-Site Request Forgery (CSRF)** attacks. Without this protection, another website could attempt to make a logged-in user's browser send a request to our application, such as deleting data or changing portfolio content. Therefore, every form that modifies data in this project needs to include `{% csrf_token %}`.

2. JSON is preferred in many modern web applications because its syntax is compact and its structure is similar to objects and arrays in JavaScript. This makes communication between a Django backend and a browser frontend easier, because a JSON response can be processed directly using `response.json()` or `JSON.parse()`.

As a simple example, this is what the Experience data in JSON look like:

```json
{
  "title": "PBP Teaching Assistant",
  "category": "part-time",
  "description": "Helping students understand web development."
}
```

Compared with XML, JSON usually has several advantages:

- The data size tends to be smaller because JSON does not require as many opening and closing tags as XML.
- It is easier for developers to read and write.
- It works naturally with JavaScript, which is commonly used on the web frontend.
- It is simpler to use in REST APIs and data exchange between services.
- JSON parsing is generally more practical for simple web application needs.

However, XML is not a bad format. XML is still useful when an application requires complex document structures, namespaces, attributes, or integration with legacy systems that already use XML. Therefore, JSON is more popular not because it is always better, but because it is more practical for the API and modern web application needs of this project.

3. In this project, the experience JSON endpoint is handled by the `get_experiences_json` function in `main/views.py`. The flow is as follows:

1. The client sends a request to an endpoint, such as `/api/experiences/`.
2. Django matches the URL in `main/urls.py` and forwards the request to the `get_experiences_json` view.
3. The view retrieves data from the database using the Django ORM through `Experience.objects.all()`.
4. If a `category` parameter is provided, the queryset can be filtered first.
5. The queryset is passed to `serializers.serialize("json", experiences)`.
6. Django converts the model objects and Python queryset into a JSON string containing the data fields and values.
7. The string is returned using `HttpResponse` with `content_type="application/json"`.
8. The client can read the response as JSON and use it for display or further processing.

Serialization is necessary because Django model objects and a `QuerySet` are not formats that can be sent directly over HTTP as JSON. They still contain Python and Django-specific internal behavior and structure, while the client needs data in a structured text format with a standard representation.

Through serialization, data such as UUIDs, categories, descriptions, and dates are converted into a JSON representation that can be understood by a browser or another application. This process also separates the data representation from the internal model object, so the database model itself does not have to be sent directly to the client.

On the Experience page, this project also performs deserialization after the data is converted into JSON. The JSON data is converted back into model objects before being passed to the template. Meanwhile, the `/api/experiences/` endpoint returns the serialized result directly so that it can be consumed by another client.


### AI Disclosure
I used AI for helping how to write a proper and scalable unit tests to ensure my application works and behaves like i want it to be. I also used AI to ask "does endline effects Django syntax writing when rendered in HTML files?".

**PROMPT**: How to create unit tests for testing application in Django?
**PURPOSE**: To know how does the Unit Test works in Django and how to configure it
**OUTPUT**: Step by step explanation on how the Django Unit Test can help development process and quality testing, what classes or packages in mainly used when writing Unit Test, and lastly how to make one

**PROMPT**: Django syntax in HTML and does a newline effects the runtime?
**PURPOSE**: I spesifically asked this because I got an unclear and ambiguous error saying that some URL is not loaded or registered, whereas I already registered it.
**OUTPUT**: Correction and comparison between using a newline in Django syntax for HTML files and how to prevent it


As i always said in my previous AI Disclosure, i don't 100% fully trusted in these AI answers, i still keep checking the official docs of Django [Django Template Syntax](https://docs.djangoproject.com/en/6.1/ref/templates/language/) and also read from the Medium blog for best practices in writing Django templates language for better understanding [Medium - Django Templates Best Practices](https://dev.to/bharat_solanke_8e45411fa6/mastering-whitespace-and-newlines-in-django-templates-the-ultimate-guide-5eii). Hence, i can write and compare the AI answers to the actual documentation and experiences from the Django developer community which statistically more accurate and reliable.
