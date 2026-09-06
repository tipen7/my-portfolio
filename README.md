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
- [x] Initialized Python virtual environment (`venv`)
- [x] Created `requirements.txt` and installed project dependencies
- [x] Configured `.gitignore` for version control
- [x] Added `.env.example` and `.env.prod.example` for environment variable guidance
- [x] Initialized Django app (`myportofolio`)
- [x] Configured baseline settings in `settings.py`
- [x] Styled and reformatted README.md
- [x] Created `static/` folder to hold css (`static/css/`) and images (`static/img/`)
- [x] Created `templates/` folder for html (`index/html`)
- [x] Reconfigure the project structure `myportofolio` -> `portofolio`
- [x] Changed some setup matching the `portofolio` directory name
- [x] Updated .env.prod for deployment
- [x] Removed SECRET_KEY exposure and set DEBUG = False for production purpose
- [x] Updated .env.prod.example for Django secret key
- [X] Created a simple and minimalist Navigation Bar
- [x] Created About Section
- [x] Created Skills Section
---

### Tugas 1
1. Yes, i used one of the HTML5 tags mentioned in the question, which is `<section>`, this tags helps for improving SEO, creates document outline (elements inside the tags are grouped together such as paragraph, images, etc. which gives a readable outline), also i used this spesifically for smooth-scrolling behaviour whenever user clicks my navigation bar tab (Skills) that will redirects them to the Skills section smoothly.

2. When dealing with responsiveness when i creating a website, my top concern is about how each of the website's elements corresponds to the display for all three categorial devices viewport which is mobile (>=375px), tablet (>=768px), and dekstop (>=1024px). List of elements that usually needs a concern is assets (icons, images, etc. ), boxes/container, typography (spacing, size, weight, etc.), layouting (grid, flexbox, etc.)

3. The limitation i felt for this static web that I have created is that it is only pure HTML and CSS without some logic or interactiveness. We as a developer must ensure that we can satisfy user experience, not only the user interfaces. Such as there are users who like to view a website in a dark mode, write and sends an email directly in the website (CTAs), and other things. With that being said, my next improvements for ensuring the dynamic functionality of this website is adding a new interactiveness such as Dark/Light mode, contact person, and also a Projects section where user can view all my created projects and can redirect them to the Github repo (if its not private) or the deployment link.

## AI Declaration
I used AI for helping me in development, but its only a little comparing to my own work, i can say that i used 5% of AI (for ONLY CSS purpose) and the 95% rest was me. Primarily, i used AI for helping me in making sure the responsiveness of my website is spot on, such as list of CSS syntax or keywords that are used for media query, uses `rem` measurement for dynamic sizing, `clamp()` function, For the model, i use Gemini Flash 3.6 and my prompting strategy is:
- Asking the AI for a syntax or keywords that have a functionality of what i wanted to do (e.g. What are CSS syntax keywords to do media query for responsiveness purpose?) -> Output: List of CSS syntax spesifically ones that are responsible for responsiveness -> Purpose: To make my website responsive 
- Asking the AI how to use a syntax (e.g. How to use clamp() function and what does it do?) -> Output: Visual of using a clamp() function to an elements such as text -> Purpose: To know how a function works

Sometimes, when following the AI recommendation, it did not work as it said to. If this happens, i will go to the website documentation for CSS such as [W3Schools](https://www.w3schools.com/cssref/index.php) and [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference). If im stuck or lazy to read the entire documentation just to search for how to center a div, i will go to YouTube to watch CSS Tutorials or enter a spesific search on what i need to do e.g. "how to make responsive layout CSS". The YouTube videos i watched are [CSS Responsive Layout](https://youtu.be/yU7jJ3NbPdA?si=E7CwNNOM4lAxDEmA), [CSS Selectors](https://youtu.be/l1mER1bV0N0?si=Z4OB6uIpAR3p3s03), [CSS Flexbox](https://youtu.be/fYq5PXgSsbE?si=I32WUmeiHyIb_QC8).

And for the rest of the development, i work alone, and here is my step-by-step thinking breakdown:
1. Create a visual of my website on Figma sections-separated for mobile, desktop, and tablet display
2. For each of the sections, i will look over the overall structure such as how many `<div>` does this section need, does this section needs a `<section>` wrapper or `<article>` wrapper, do i use a `<h1>` tag, `<h2>` tag or others, etc.
3. After determining the requirements structure needed for a section, then i will think about the user experience, e.g. does this button needs a bright or dark colour? does this paragraph readable? does this hover animation too much or less?
4. Lastly, after the questions were answered, then i will implement it step-by-step starting with the HTML structure, CSS styling, and make it responsive. I always make sure to run `python manage.py check` to check of errors, bugs, or other things and make sure it runs without any errors AND look exactly like what i want with `python manage.py runserver`.