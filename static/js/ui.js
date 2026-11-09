/* ==========================================================================
   ui.js — shared front-end runtime for the Gojek-style design system.
   Provides: theme toggle · toast · dropdown · ripple · scroll reveal ·
   modal focus handling · confirm dialog · password toggle · search clear ·
   back-to-top · flash-message bridge · fetch/DOM helpers (window.UI).
   ========================================================================== */
(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const SVG_NS = "http://www.w3.org/2000/svg";
  let uidCounter = 0;
  const uid = (prefix = "ui") => `${prefix}-${++uidCounter}`;

  /* ------------------------------ DOM helpers ------------------------------ */
  function icon(name, className = "") {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", `icon ${className}`.trim());
    svg.setAttribute("aria-hidden", "true");
    const use = document.createElementNS(SVG_NS, "use");
    use.setAttribute("href", `#i-${name}`);
    svg.appendChild(use);
    return svg;
  }

  function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
      if (value === undefined || value === null || value === false) continue;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else node.setAttribute(key, value === true ? "" : value);
    }
    node.append(...children.flat().filter((child) => child !== null && child !== undefined));
    return node;
  }

  // Always uses textContent, so API data can never become markup.
  function addText(parent, tag, text, className) {
    const node = el(tag, { class: className, text: text ?? "" });
    parent.appendChild(node);
    return node;
  }

  function safeExternalUrl(value) {
    if (!value) return "";
    try {
      const url = new URL(value, window.location.origin);
      return ["http:", "https:"].includes(url.protocol) ? url.href : "";
    } catch {
      return "";
    }
  }

  // Fills a card media box with the image, or a placeholder icon when the URL is
  // missing/unsafe or the image fails to load.
  function mediaImage(media, url, alt, fallbackIcon) {
    const showFallback = () => {
      media.classList.add("item-card__media--empty");
      media.querySelector("img")?.remove();
      media.prepend(icon(fallbackIcon, "icon--xl"));
    };
    const safeUrl = safeExternalUrl(url);
    if (!safeUrl) return showFallback();
    const image = el("img", { src: safeUrl, alt, loading: "lazy" });
    image.addEventListener("error", showFallback, { once: true });
    media.prepend(image);
  }

  function getCookie(name) {
    const row = document.cookie.split("; ").find((value) => value.startsWith(`${name}=`));
    return row ? decodeURIComponent(row.slice(name.length + 1)) : "";
  }

  function apiErrorMessage(data, status) {
    const messages = Object.entries(data || {}).flatMap(([field, value]) =>
      (Array.isArray(value) ? value : [value])
        .filter((message) => typeof message === "string")
        .map((message) => (field === "detail" || field === "non_field_errors" ? message : `${field}: ${message}`)),
    );
    return messages.join(" ") || `Terjadi kesalahan (status ${status}).`;
  }

  async function apiRequest(url, method, payload) {
    const response = await fetch(url, {
      method,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: payload === undefined ? undefined : JSON.stringify(payload),
    });
    if (response.status === 204) return null;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(apiErrorMessage(data, response.status));
    return data;
  }

  function setBusy(button, busy) {
    if (!button) return;
    button.disabled = busy;
    if (busy) button.setAttribute("aria-busy", "true");
    else button.removeAttribute("aria-busy");
  }

  /* --------------------------------- Theme --------------------------------- */
  const THEME_KEY = "theme";

  function currentTheme() {
    const explicit = document.documentElement.dataset.theme;
    if (explicit) return explicit;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(THEME_KEY, theme); } catch { /* storage may be blocked */ }
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.setAttribute("aria-pressed", String(theme === "dark"));
      button.setAttribute("aria-label", theme === "dark" ? "Aktifkan mode terang" : "Aktifkan mode gelap");
    });
  }

  function initTheme() {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => applyTheme(currentTheme() === "dark" ? "light" : "dark"));
    });
    applyTheme(currentTheme());
  }

  /* --------------------------------- Toast --------------------------------- */
  const TOAST_ICONS = { success: "check-circle", error: "alert-circle", warning: "alert-triangle", info: "info" };
  const MAX_TOASTS = 4;

  function toastRegion() {
    let region = document.getElementById("toast-region");
    if (!region) {
      region = el("div", { id: "toast-region", popover: "manual", "aria-live": "polite", "aria-atomic": "false" });
      document.body.appendChild(region);
    }
    return region;
  }

  function popoverOpen(node) {
    try { return node.matches(":popover-open"); } catch { return true; }
  }

  function removeToast(toast) {
    if (!toast.isConnected || toast.classList.contains("is-leaving")) return;
    clearTimeout(toast._timer);
    toast.classList.add("is-leaving");
    const finish = () => {
      const region = toast.parentElement;
      toast.remove();
      if (region && !region.children.length && popoverOpen(region)) {
        try { region.hidePopover(); } catch { /* unsupported */ }
      }
    };
    toast.addEventListener("animationend", finish, { once: true });
    setTimeout(finish, 400); // safety net when animations are disabled
  }

  function showToast(title, message, type = "normal", duration) {
    const kind = TOAST_ICONS[type] ? type : "info";
    const total = duration ?? (kind === "error" ? 5500 : 3500);
    const region = toastRegion();

    const close = el("button", { type: "button", class: "icon-btn icon-btn--sm", "aria-label": "Tutup notifikasi" }, icon("x", "icon--sm"));
    const toast = el(
      "div",
      { class: `toast toast--${kind}`, role: kind === "error" ? "alert" : "status", style: `--toast-duration:${total}ms` },
      el("span", { class: "toast__icon" }, icon(TOAST_ICONS[kind])),
      el("div", {}, el("p", { class: "toast__title", text: title }), message ? el("p", { class: "toast__message", text: message }) : null),
      close,
      el("span", { class: "toast__progress", "aria-hidden": "true" }),
    );

    let remaining = total;
    let startedAt = 0;
    const start = () => {
      startedAt = Date.now();
      toast._timer = setTimeout(() => removeToast(toast), remaining);
    };
    const pause = () => {
      clearTimeout(toast._timer);
      remaining -= Date.now() - startedAt;
    };
    toast.addEventListener("pointerenter", pause);
    toast.addEventListener("pointerleave", start);
    toast.addEventListener("focusin", pause);
    toast.addEventListener("focusout", start);
    close.addEventListener("click", () => removeToast(toast));

    while (region.querySelectorAll(".toast:not(.is-leaving)").length >= MAX_TOASTS) {
      removeToast(region.querySelector(".toast:not(.is-leaving)"));
    }
    region.appendChild(toast);

    // Re-open the region so it stacks above any modal that is currently open.
    try {
      if (popoverOpen(region) && document.querySelector(".modal:popover-open")) region.hidePopover();
      if (!popoverOpen(region)) region.showPopover();
    } catch { }

    start();
    return toast;
  }

  function dismissToast() {
    document.querySelectorAll("#toast-region .toast").forEach(removeToast);
  }

  /* ------------------------------- Dropdown -------------------------------- */
  const openDropdowns = new Set();

  function closeAllDropdowns(except) {
    openDropdowns.forEach((close) => {
      if (close !== except) close();
    });
  }

  function enhanceSelect(select) {
    if (select.dataset.enhanced || select.hasAttribute("data-native") || select.multiple) return;
    select.dataset.enhanced = "1";

    const wrap = el("div", { class: "dropdown" });
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");

    const listId = uid("dd-list");
    const label = el("span", { class: "dropdown__label" });
    const trigger = el(
      "button",
      {
        type: "button",
        class: "dropdown__trigger",
        role: "combobox",
        "aria-haspopup": "listbox",
        "aria-expanded": "false",
        "aria-controls": listId,
      },
      label,
      icon("chevron-down", "dropdown__chevron"),
    );
    const list = el("ul", { class: "dropdown__list", role: "listbox", id: listId, tabindex: "-1" });
    const panel = el("div", { class: "dropdown__panel" }, list);
    wrap.append(trigger, panel);

    // Accessible name: <label for>, aria-label, or fall back to the current value.
    const externalLabel = select.id ? document.querySelector(`label[for="${CSS.escape(select.id)}"]`) : null;
    if (externalLabel) {
      externalLabel.id ||= uid("dd-label");
      trigger.setAttribute("aria-labelledby", externalLabel.id);
      externalLabel.addEventListener("click", () => trigger.focus());
    } else if (select.getAttribute("aria-label")) {
      trigger.setAttribute("aria-label", select.getAttribute("aria-label"));
    }

    const options = [...select.options].map((option, index) => {
      const item = el(
        "li",
        {
          class: "dropdown__option",
          role: "option",
          id: `${listId}-${index}`,
          "aria-selected": "false",
          "aria-disabled": option.disabled ? "true" : null,
          style: `--i:${index}`,
        },
        el("span", { text: option.textContent.trim() }),
        icon("check", "icon--sm"),
      );
      list.appendChild(item);
      return item;
    });

    let activeIndex = -1;
    let typeahead = "";
    let typeaheadTimer;

    function sync() {
      const selected = select.selectedIndex;
      label.textContent = select.options[selected]?.textContent.trim() ?? "";
      options.forEach((item, index) => item.setAttribute("aria-selected", String(index === selected)));
    }

    function setActive(index) {
      options[activeIndex]?.classList.remove("is-active");
      activeIndex = Math.max(0, Math.min(options.length - 1, index));
      const item = options[activeIndex];
      if (!item) return;
      item.classList.add("is-active");
      trigger.setAttribute("aria-activedescendant", item.id);
      item.scrollIntoView({ block: "nearest" });
    }

    function open() {
      if (wrap.classList.contains("is-open") || select.disabled) return;
      closeAllDropdowns();
      wrap.classList.add("is-open");
      trigger.setAttribute("aria-expanded", "true");
      setActive(select.selectedIndex);
      openDropdowns.add(close);
    }

    function close() {
      if (!wrap.classList.contains("is-open")) return;
      wrap.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
      trigger.removeAttribute("aria-activedescendant");
      options[activeIndex]?.classList.remove("is-active");
      openDropdowns.delete(close);
    }

    function choose(index) {
      if (options[index]?.getAttribute("aria-disabled") === "true") return;
      const changed = select.selectedIndex !== index;
      select.selectedIndex = index;
      sync();
      close();
      trigger.focus();
      if (changed) select.dispatchEvent(new Event("change", { bubbles: true }));
    }

    trigger.addEventListener("click", () => (wrap.classList.contains("is-open") ? close() : open()));

    trigger.addEventListener("keydown", (event) => {
      const isOpen = wrap.classList.contains("is-open");
      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          isOpen ? setActive(activeIndex + 1) : open();
          break;
        case "ArrowUp":
          event.preventDefault();
          isOpen ? setActive(activeIndex - 1) : open();
          break;
        case "Home":
          if (isOpen) { event.preventDefault(); setActive(0); }
          break;
        case "End":
          if (isOpen) { event.preventDefault(); setActive(options.length - 1); }
          break;
        case "Enter":
        case " ":
          event.preventDefault();
          isOpen ? choose(activeIndex) : open();
          break;
        case "Escape":
          if (isOpen) { event.preventDefault(); event.stopPropagation(); close(); }
          break;
        case "Tab":
          close();
          break;
        default:
          if (event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
            typeahead += event.key.toLowerCase();
            clearTimeout(typeaheadTimer);
            typeaheadTimer = setTimeout(() => (typeahead = ""), 600);
            const match = options.findIndex((item) => item.textContent.trim().toLowerCase().startsWith(typeahead));
            if (match >= 0) { open(); setActive(match); }
          }
      }
    });

    list.addEventListener("pointerdown", (event) => event.preventDefault());
    list.addEventListener("click", (event) => {
      const index = options.indexOf(event.target.closest(".dropdown__option"));
      if (index >= 0) choose(index);
    });
    list.addEventListener("pointermove", (event) => {
      const index = options.indexOf(event.target.closest(".dropdown__option"));
      if (index >= 0 && index !== activeIndex) setActive(index);
    });

    select.form?.addEventListener("reset", () => setTimeout(sync));
    select._syncDropdown = sync;
    sync();
  }

  function syncDropdowns(root = document) {
    root.querySelectorAll("select").forEach((select) => select._syncDropdown?.());
  }

  /* ------------------------------ Confirm dialog ---------------------------- */
  let confirmState;

  function confirmDialog({
    title = "Are you sure?",
    message = "",
    confirmLabel = "Yes, continue",
    cancelLabel = "Cancel",
    tone = "danger",
  } = {}) {
    if (!confirmState) {
      const modal = el("div", { id: "confirm-modal", class: "modal modal--sm", popover: "auto", role: "alertdialog", "aria-labelledby": "confirm-title", "aria-describedby": "confirm-message" });
      const iconBox = el("span", { class: "modal__icon" });
      const titleNode = el("h2", { id: "confirm-title", class: "modal__title" });
      const messageNode = el("p", { id: "confirm-message", class: "modal__intro" });
      const cancel = el("button", { type: "button", class: "btn btn--ghost", "data-autofocus": "" });
      const ok = el("button", { type: "button", class: "btn btn--danger" });
      modal.append(
        el("div", { class: "modal__header" }, iconBox, el("div", { class: "modal__titles" }, titleNode)),
        el("div", { class: "modal__body" }, messageNode, el("div", { class: "modal__footer" }, cancel, ok)),
      );
      document.body.appendChild(modal);
      confirmState = { modal, iconBox, titleNode, messageNode, cancel, ok, resolve: null, result: false };

      ok.addEventListener("click", () => { confirmState.result = true; modal.hidePopover(); });
      cancel.addEventListener("click", () => modal.hidePopover());
      modal.addEventListener("toggle", (event) => {
        if (event.newState !== "closed") return;
        confirmState.resolve?.(confirmState.result);
        confirmState.resolve = null;
      });
    }

    const state = confirmState;
    state.resolve?.(false);
    state.result = false;
    state.iconBox.className = `modal__icon${tone === "danger" ? " modal__icon--danger" : ""}`;
    state.iconBox.replaceChildren(icon(tone === "danger" ? "trash" : "info", "icon--lg"));
    state.titleNode.textContent = title;
    state.messageNode.textContent = message;
    state.cancel.textContent = cancelLabel;
    state.ok.textContent = confirmLabel;
    state.ok.className = `btn ${tone === "danger" ? "btn--danger" : ""}`;

    return new Promise((resolve) => {
      state.resolve = resolve;
      state.modal.showPopover();
    });
  }

  /* --------------------------- Progressive widgets -------------------------- */
  function initRipple() {
    document.addEventListener("pointerdown", (event) => {
      const button = event.target.closest(".btn");
      if (!button || button.disabled || reduceMotion) return;
      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 2;
      const ripple = el("span", { class: "btn__ripple", "aria-hidden": "true" });
      ripple.style.cssText = `width:${size}px;height:${size}px;left:${event.clientX - rect.left - size / 2}px;top:${event.clientY - rect.top - size / 2}px`;
      button.appendChild(ripple);
      ripple.addEventListener("animationend", () => ripple.remove(), { once: true });
    });
  }

  function initReveal() {
    const targets = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      targets.forEach((target) => target.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }),
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );
    targets.forEach((target) => observer.observe(target));
  }

  function initTilt() {
    if (reduceMotion || !window.matchMedia("(pointer: fine)").matches) return;
    document.querySelectorAll("[data-tilt]").forEach((node) => {
      node.addEventListener("pointermove", (event) => {
        const rect = node.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        node.style.transform = `perspective(900px) rotateY(${x * 12}deg) rotateX(${-y * 12}deg)`;
      });
      node.addEventListener("pointerleave", () => { node.style.transform = ""; });
    });
  }

  function initPasswordToggle() {
    document.querySelectorAll('input[type="password"]').forEach((input) => {
      const wrap = el("div", { class: "password-field" });
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
      const toggle = el("button", { type: "button", class: "icon-btn icon-btn--sm", "aria-pressed": "false", "aria-label": "Tampilkan kata sandi" }, icon("eye"));
      wrap.appendChild(toggle);
      toggle.addEventListener("click", () => {
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        toggle.setAttribute("aria-pressed", String(show));
        toggle.setAttribute("aria-label", show ? "Sembunyikan kata sandi" : "Tampilkan kata sandi");
        toggle.replaceChildren(icon(show ? "eye-off" : "eye"));
      });
    });
  }

  function initSearchClear() {
    document.querySelectorAll(".input-icon").forEach((wrap) => {
      const input = wrap.querySelector("input");
      if (!input) return;
      const clear = el("button", { type: "button", class: "icon-btn icon-btn--sm input-icon__clear", "aria-label": "Hapus pencarian", tabindex: "-1" }, icon("x", "icon--sm"));
      wrap.appendChild(clear);
      const update = () => wrap.classList.toggle("has-value", input.value.length > 0);
      input.addEventListener("input", update);
      clear.addEventListener("click", () => {
        input.value = "";
        update();
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
      });
      update();
    });
  }

  function initModals() {
    document.addEventListener("toggle", (event) => {
      const modal = event.target;
      if (!(modal instanceof HTMLElement) || !modal.classList.contains("modal") || event.newState !== "open") return;
      const focusTarget = modal.querySelector("[data-autofocus], input:not([type=hidden]), textarea, select, button.btn");
      if (focusTarget) focusTarget.focus({ preventScroll: true });
    }, true);
  }

  function initScrollEffects() {
    const navbar = document.querySelector(".navbar");
    const toTop = el("button", { type: "button", class: "icon-btn to-top", "aria-label": "Kembali ke atas" }, icon("arrow-up"));
    document.body.appendChild(toTop);
    toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" }));

    let ticking = false;
    const update = () => {
      navbar?.classList.toggle("is-scrolled", window.scrollY > 24);
      toTop.classList.toggle("is-visible", window.scrollY > 600);
      ticking = false;
    };
    window.addEventListener("scroll", () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  function initFlashMessages() {
    const levelMap = { success: ["Berhasil", "success"], error: ["Gagal", "error"], warning: ["Perhatian", "warning"], info: ["Informasi", "info"], debug: ["Informasi", "info"] };
    document.querySelectorAll("[data-flash] [data-level]").forEach((node, index) => {
      const [title, type] = levelMap[node.dataset.level] || levelMap.info;
      setTimeout(() => showToast(title, node.textContent.trim(), type), 250 + index * 150);
    });
  }

  /* ------------------------------ Tech icons ------------------------------- */
  // Real brand icons (devicon, bundled in static/img/tech). Unknown names get a generic glyph.
  const TECH_ICONS = new Set(("androidstudio angularjs aws azure bootstrap bun c cplusplus csharp css3 d3js dart denojs django docker " +
    "express fastapi figma firebase flask flutter git github go googlecloud gradle graphql heroku html5 java javascript jest jupyter " +
    "kotlin kubernetes laravel linux matlab maven mongodb mysql nextjs nginx nodejs numpy nuxtjs opencv pandas php postgresql postman " +
    "prisma python pytorch r rails react redis redux ruby rust sass scikitlearn selenium spring sqlite supabase svelte swift tailwindcss " +
    "tensorflow threejs typescript unity vercel vite vuejs webpack").split(" "));
  const TECH_ALIASES = {
    "c++": "cplusplus", cpp: "cplusplus", "c#": "csharp", golang: "go", js: "javascript", ts: "typescript",
    next: "nextjs", node: "nodejs", postgres: "postgresql", psql: "postgresql", reactjs: "react", vue: "vuejs",
    angular: "angularjs", tailwind: "tailwindcss", html: "html5", css: "css3", expressjs: "express", mongo: "mongodb",
    k8s: "kubernetes", gcp: "googlecloud", amazonwebservices: "aws", sklearn: "scikitlearn", deno: "denojs",
    nuxt: "nuxtjs", ror: "rails", rubyonrails: "rails", springboot: "spring", three: "threejs", d3: "d3js",
  };

  function techSlug(name) {
    const raw = String(name ?? "").toLowerCase().trim();
    if (TECH_ALIASES[raw]) return TECH_ALIASES[raw];
    const stripped = raw.replace(/[^a-z0-9]/g, "");
    const slug = TECH_ALIASES[stripped] || stripped;
    return TECH_ICONS.has(slug) ? slug : "";
  }

  function techChip(name) {
    const slug = techSlug(name);
    const fallback = () => el("span", { class: "chip__icon chip__icon--fallback", "aria-hidden": "true" }, icon("code"));
    const chip = el("span", { class: "chip chip--tech" });
    if (slug) {
      const image = el("img", {
        class: "chip__icon", src: `${window.TECH_ICON_BASE || "/static/img/tech/"}${slug}.svg`,
        alt: "", width: "22", height: "22", loading: "lazy",
      });
      image.addEventListener("error", () => image.replaceWith(fallback()), { once: true });
      chip.appendChild(image);
    } else {
      chip.appendChild(fallback());
    }
    chip.appendChild(el("span", { text: String(name) }));
    return chip;
  }

  function initTechChips() {
    document.querySelectorAll("[data-tech-chips]").forEach((box) => {
      box.dataset.techChips.split(",").forEach((name) => box.appendChild(techChip(name.trim())));
    });
  }

  /* -------------------------------- Navbar --------------------------------- */
  function initNavbar() {
    const navbar = document.querySelector("[data-navbar]");
    if (!navbar) return;
    const menus = [...navbar.querySelectorAll("[data-menu]")];
    const burger = navbar.querySelector(".nav-burger");
    const desktop = window.matchMedia("(min-width: 60rem)");
    const hoverCapable = window.matchMedia("(hover: hover) and (pointer: fine)");
    const triggerOf = (menu) => menu.querySelector(".nav-trigger, .user-menu__trigger");
    const timers = new WeakMap();

    function refresh() {
      navbar.classList.toggle("has-open", menus.some((menu) => menu.classList.contains("is-open")));
    }

    function setOpen(menu, open) {
      clearTimeout(timers.get(menu));
      menu.classList.toggle("is-open", open);
      triggerOf(menu).setAttribute("aria-expanded", String(open));
      refresh();
    }

    const closeAll = (except) => menus.forEach((menu) => menu !== except && setOpen(menu, false));

    menus.forEach((menu) => {
      const trigger = triggerOf(menu);
      trigger.addEventListener("click", () => {
        const open = !menu.classList.contains("is-open");
        closeAll(menu);
        setOpen(menu, open);
      });
      
      menu.addEventListener("pointerenter", (event) => {
        if (event.pointerType !== "mouse" || !hoverCapable.matches) return;
        clearTimeout(timers.get(menu));
        timers.set(menu, setTimeout(() => { closeAll(menu); setOpen(menu, true); }, 70));
      });
      menu.addEventListener("pointerleave", (event) => {
        if (event.pointerType !== "mouse") return;
        clearTimeout(timers.get(menu));
        timers.set(menu, setTimeout(() => setOpen(menu, false), 180));
      });
      menu.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && menu.classList.contains("is-open")) {
          setOpen(menu, false);
          trigger.focus();
        } else if (event.key === "ArrowDown" && event.target === trigger) {
          event.preventDefault();
          setOpen(menu, true);
          menu.querySelector(".mega__link, .menu-item")?.focus();
        }
      });
      menu.addEventListener("focusout", (event) => {
        if (!menu.contains(event.relatedTarget)) setOpen(menu, false);
      });
    });

    document.addEventListener("pointerdown", (event) => {
      if (!event.target.closest?.("[data-menu]")) closeAll();
    });

    /* Mobile drawer */
    function setMobile(open) {
      navbar.classList.toggle("is-mobile-open", open);
      document.body.classList.toggle("menu-open", open);
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? "Tutup menu" : "Buka menu");
    }

    burger.addEventListener("click", () => setMobile(!navbar.classList.contains("is-mobile-open")));
    navbar.querySelectorAll(".mobile-menu a").forEach((link) => link.addEventListener("click", () => setMobile(false)));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && navbar.classList.contains("is-mobile-open")) { setMobile(false); burger.focus(); }
    });
    desktop.addEventListener("change", (event) => { if (event.matches) setMobile(false); });

    navbar.querySelectorAll("[data-accordion]").forEach((group) => {
      const trigger = group.querySelector(".mobile-group__trigger");
      trigger.addEventListener("click", () => {
        const open = group.classList.toggle("is-open");
        trigger.setAttribute("aria-expanded", String(open));
      });
    });
  }

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-scroll-top]")) return;
    event.preventDefault();
    window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".dropdown")) closeAllDropdowns();
  });

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initNavbar();
    initTechChips();
    document.querySelectorAll("select").forEach(enhanceSelect);
    initPasswordToggle();
    initSearchClear();
    initRipple();
    initReveal();
    initTilt();
    initModals();
    initScrollEffects();
    initFlashMessages();
  });

  window.UI = {
    icon, el, addText, safeExternalUrl, mediaImage, techChip, getCookie, apiRequest, apiErrorMessage,
    setBusy, syncDropdowns, enhanceSelect, confirm: confirmDialog, showToast,
  };
  window.showToast = showToast;
  window.dismissToast = dismissToast;
})();
