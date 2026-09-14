# My Portfolio Project
---

## 👤 Author Information

| Field | Details |
| :--- | :--- |
| **Name** | Steven Dyanizha Ananda |
| **NPM** | 2506616112 |
| **Class** | A |

---

## 🚀 Progress Update
 - [x] Completed Tugas 2

---

### Tugas 2

# Django Architecture Notes

This document explains three core Django concepts used throughout this portfolio project: the **MVT request lifecycle**, the rationale for **persisting data in models instead of hardcoding it**, and the distinction between **`makemigrations`** and **`migrate`**.

---

## Table of Contents



## 1. Django MVT Architecture

Django follows the **MVT (Model-View-Template)** pattern means that every request that hits this portfolio site gets processed by a pipeline before a response is rendered back to the browser.

### Flow Diagram

```
User opens the website (URL)
        │
        ▼
Browser sends an HTTP GET request
        │
        ▼
Django receives the request and checks the PROJECT urls.py
        │
        ▼
URL is matched via include() and dispatched to the corresponding APP urls.py
        │
        ▼
The matched URL pattern resolves to its associated View
        │
        ▼
View executes queries the database (retrieve / create / update / delete)
        │
        ▼
View then loads the requested Template (HTML file) and insert context data
        │
        ▼
The rendered HTML is returned as an HTTP response to the user browser
```

### Step-by-Step Breakdown

| Step | Component | Responsibility |
| --- | --- | --- |
| 1   | **Browser** | Sends an HTTP GET (or POST) request to a specific URL. |
| 2   | **Project `urls.py`** | Acts as the root URL dispatcher for the entire project. |
| 3   | **`include()`** | Finds a  matching URL patterns to an app's `urls.py`, keeping routing modular and well scoped. |
| 4   | **App `urls.py`** | Maps the specific path to the exact View responsible for handling it. |
| 5   | **View** | Contains the business logic. Performs the necessary database operation(s) via the ORM (`Model.objects.filter()`, `.create()`, `.update()`, `.delete()`, etc.). |
| 6   | **Template** | An HTML file that the View renders using `render()` is filled with context data returned from the query. |
| 7   | **Response** | The final rendered HTML is sent back to the client and displayed in the browser. |

### Why This Matters

- Models handle data, Views handle logic, Templates handle presentation. Each layer can be modified independently.  
- Because every request follows the same pipeline, debugging becomes easier since its just a matter of tracing a single and consistent path (`urls.py` → `views.py` → `templates/`).
- New routes and features can be added without disturbing existing logic, since routing and logic are grouped.

---

## 2. Why Data Belongs in `models.py`, Not HTML

### Scalability

Data stored in the database can grow uncertainly without requiring changes to the codebase. Adding a new portfolio project, blog post, or skill entry becomes a matter of inserting a new row, not editing and redeploying HTML.

### Accessibility

Data stored as structured model instances can be:

- Reused across multiple templates and views without duplication.
- Exposed through an API (e.g. Django REST Framework) for consumption by other clients (mobile apps, SPAs, third-party integrations).
- Queried programmatically, rather than being locked inside static markup.

### Validation and Testing

Models allow Django to enforce **data integrity at the schema level** via field types, constraints, and custom `clean()`/`validate()` methods. This also makes the data testable in isolation using Django's testing framework (`TestCase`, model factories, fixtures) and also protected against malformed or inconsistent input, which raw HTML content has no mechanism to guard against.

### Filtering and Searching

The Django ORM allows data to be filtered, sorted, aggregated, and searched efficiently (`filter()`, `exclude()`, `annotate()`, `Q` objects, full-text search, etc.). Hardcoded HTML content offers none of this, any "filtering" would require manually rewriting markup.

### Summary Table

| Criteria | Hardcoded HTML | Model-Backed Data |
| --- | --- | --- |
| Scalability | ❌ Manual edits per entry | ✅ Insert/update rows dynamically |
| Reusability | ❌ Duplicated across templates | ✅ Queried and reused anywhere |
| Validation | ❌ None | ✅ Enforced at the schema level |
| Searchability | ❌ Not possible | ✅ Native ORM filtering/search |
| API-readiness | ❌ Requires rewrite | ✅ Serializable out of the box |

---

## 3. `makemigrations` vs `migrate`

### `makemigrations`

- **Detects** changes made to your models (new fields, removed fields, changed types, new models, etc.) by comparing the current state of `models.py` against the most recent existing migration files.
- **Generates** a new migration file (e.g. `0004_projects.py`) that describes those changes as a set of operations, it does **not** touch the actual database.
- Think of it as writing the *instructions* for a change, **WITHOUT** executing them yet.

### `migrate`

- **Reads** the migration files (including the one just generated by `makemigrations`) and checks which ones have not yet been applied to the database, tracked via Django's internal `django_migrations` table.
- **Executes** the pending migration operations against the actual database schema creating tables, altering columns, adding indexes, etc.
- Think of it as *applying* the instructions that `makemigrations` wrote.

### Command Comparison

|     | `makemigrations` | `migrate` |
| --- | --- | --- |
| **Purpose** | Detects model changes and writes migration files | Applies migration files to the database |
| **Touches the database?** | No  | Yes |
| **Input** | Current `models.py` state versus last migration changes | Existing migration files |
| **Output** | New `.py` migration file(s) in `migrations/` | Actual schema changes (tables, columns, constraints) |
| **Typical order** | Run first | Run second |

### Quick Mental Model

```
models.py  ──makemigrations──▶  migration files  ──migrate──▶  database schema
   (source of truth)              (the "diff")                  (applied state)
```

---

## References

- [Django Documentation: URL](https://docs.djangoproject.com/en/stable/topics/http/urls/)
- [Django Documentation: Models](https://docs.djangoproject.com/en/stable/topics/db/models/)
- [Django Documentation: Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)



### AI Disclosure
I used AI to help me understand more about the Django architecture, especially how formally the pipeline process works. Also, AI helps me to visualize and compare the minus and plus of using `models.py` as the database rather than raw HTML file. 

**PROMPT**: Explain to me what is MVT Architecture in Django.
**PURPOSE**: To get a more visualization of how the pipeline works
**OUTPUT**: Mermaid Graph visualizing the pipeline process

**PROMPT**: Why using models.py to insert data rather than hardcoded it directly in HTML? Provide a clear explanation and compare for each aspects of security, best practices, and other relevant fields.
**PURPOSE**: To help me understand clearly on when to use what depending on the requirements.
**OUTPUT**: Comparison table that consist of when to use HTML/models.py based on a situation

**NOTES**: Even though the AI already provides a clear explanation, i initiatively do a research myself on the [Django Documentation about models](https://docs.djangoproject.com/en/6.1/topics/db/models/). Me myself do not trust AI fully, im adjusting the AI output to my own research then combine them to provide a more detailed explanation.
