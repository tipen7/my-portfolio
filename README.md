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


- [x] Implemented AJAX and changed from Python object to JSON for views that corresponds to experience and project section
- [x] Refined and redesign modal, dropdown, searchbar components

---

### Tugas 5
1. **Debouncing** is a technique that delays the execution of a function until the user stops performing an action for a certain amount of time. In our case, the search bar for Projects and Experiences section which is an AJAX search feature prevents a request from being sent every time the user presses a key. For example, when typing some word such as "software engineer" , without debouncing, the browser could send six separate requests to the server. With debouncing, the request is only sent after the user stops typing for a short period, reducing unnecessary requests and server load. This makes the search feature more efficient and responsive, yet still maintain a good user experiences. 

2. `await` is one of Javascript main keyword used to wait for an asynchronous operation such as `fetch()` to finish before continuing with the next line of code. With `await`, we can receive the Response object and then process its data, for example using `await response.json()`. If we do not use `await`, `fetch()` immediately returns a `Promise` which is a JavaScript object that relates with asynchronous calls instead of the actual response. As a result, we cannot directly access the response data before the `Promise` has been resolved. Therefore, `await` makes asynchronous code easier to read and allows us to handle the request in a sequential way.

3. XSS (Cross-Site Scripting) is an attack where an attacker manages to inject malicious JavaScript code into a web page that is then executed in the user's browser. Data displayed through JavaScript/AJAX can be more vulnerable if we insert server-provided data directly into the DOM using innerHTML without proper escaping or sanitization. In Django templates, data such as `{{ data }}` is automatically escaped by default, which helps prevent HTML or JavaScript from being executed as code. However, when using JavaScript, developers need to be more careful about how data is inserted into the DOM, such as using `textContent` for plain text. Therefore, AJAX itself is not entirely insecure, but improper handling of dynamically displayed data can create an XSS vulnerability.


### AI Disclosure
For this individual assignment, i used AI (ChatGPT) to help me learn, explore, and provide an example of AJAX operations. Besides that, i used AI to help me write some CSS styling because i am bad at making a good user interfaces, therefore i can use a bit of help. However, the AI made some mistakes that make me must to double check and make sure that gives a correct and efficient code. I also changed some of the code myself using my knowledge, such as some CSS styling i modified myself, optimized JavaScript code, etc.

**PROMPT**: Act as Senior Frontend Engineer and UI UX Specialist, help me design a good modal, form and dropdown filter components.
**OUTPUT**: Codes & UI design reference
**PURPOSE**: To serve and provide the best user experience possible

**PROMPT**: Explain simply about AJAX Django and write some code function sample.
**OUTPUT**: Simple, detailed, and structured breakdown on what is AJAX and how to apply it in Django web development
**PURPUSE**: To get a better understanding and make sure to apply the best practices before writing any code


Even though this is classified as a medium level AI usage, me as a student and an enthusiastic learner still needs to learn the concepts by myself. Hence, here is some references i used throughout working on finishing the Individual Assignment 5.

References:
[Django AJAX Request Handling][https://www.geeksforgeeks.org/python/handling-ajax-request-in-django/]
[MDN Fetch API][https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API]