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

- [x] Implemented authentication and authorization for the portfolio
- [x] Adjusting the features according to user roles
  **SUPERUSER**: All access to all features and CRUD operations
  -> Username: superusr_tipen
  -> Password: superusertipen123

  **EDITOR**: Can only view and update projects/experience also star
  -> Username: editor_tipen
  -> Password: test12345

  **USER**: Can only view and star projects
  -> Username: user_tipen
  -> Password: usertipen123

  **UNAUTHENTICATED USER**: Can only view
  
  NOTES: Unauthenticated user will be redirected to login page if trying to access a feature that requires login

- [x] Safely added guard against unauthenticated users
- [x] Altered views, urls, and forms to register new routes
- [x] Added some styling and logic in HTML files
- [x] Created `Comment` models, views, and urls for comment section for each experience

---

### AI Disclosure
For this Individual Assignment, i use AI to help me thinking about a new feature that i should implement that still involves about **Authentication and Authorization**. I also use the help of AI to help me style and design the component for `comment_section.html` and `style.css` that corresponds to it.

**PROMPT**: For this assignment, what features do you suggest to be implemented that still involve something about authentication and authorization?
**PURPOSE**: To gain more experience on web development and get used to knowing the basic implementation of common features in software/app development
**OUTPUT**: List of features recommendation -> Comments, Likes, Bookmark

**PROMPT**: Help me style and design a responsive yet interactive comment section component for experience card. Make sure its responsive.
**PURPOSE**: To rapidly increase development also learning purpose
**OUTPUT**: CSS Code for `style.css` spesifically the comment features


Besides AI Usage, i also read from Django Docs for official documentation regarding authentication and authorization, how to use Django Admin, and how to write Unit Tests for this new implemented features. For the styling necessity, as usual, i read from MDN CSS References and W3Schools for learning purpose & make sure the styling are spot on and responsive accross three devices. Last but not least, i always verify and make sure the code/suggestion that AI gived me is correct and follow the best practices.

References:
[Django Authentication and Authorization](https://docs.djangoproject.com/en/6.1/topics/auth/)
[Django Admin](https://docs.djangoproject.com/en/6.1/ref/contrib/admin/)
[Django Unit Tests](https://docs.djangoproject.com/en/6.1/topics/testing/overview/)
[MDN CSS References](https://developer.mozilla.org/en-US/docs/Web/CSS)
[W3Schools CSS](https://www.w3schools.com/css/)