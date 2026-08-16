(() => {
  "use strict";

  const STORAGE_PREFIX = "python-oop-handbook-ua";
  const PROGRESS_KEY = `${STORAGE_PREFIX}:completed`;
  const TASKS_KEY = `${STORAGE_PREFIX}:tasks`;
  const THEME_KEY = `${STORAGE_PREFIX}:theme`;
  const root = document.documentElement;
  const body = document.body;

  const readSet = (key) => {
    try {
      const value = JSON.parse(localStorage.getItem(key) || "[]");
      return new Set(Array.isArray(value) ? value : []);
    } catch {
      return new Set();
    }
  };

  const writeSet = (key, value) => {
    localStorage.setItem(key, JSON.stringify([...value]));
  };

  const completed = readSet(PROGRESS_KEY);
  const checkedTasks = readSet(TASKS_KEY);

  function setTheme(theme) {
    root.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
    document.querySelectorAll(".theme-toggle").forEach((button) => {
      button.setAttribute("aria-label", theme === "dark" ? "Увімкнути світлу тему" : "Увімкнути темну тему");
      if (button.classList.contains("desktop-theme")) {
        button.title = theme === "dark" ? "Світла тема" : "Темна тема";
      }
    });
  }

  const savedTheme = localStorage.getItem(THEME_KEY);
  const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  setTheme(savedTheme || preferredTheme);

  document.querySelectorAll(".theme-toggle").forEach((button) => {
    button.addEventListener("click", () => setTheme(root.dataset.theme === "dark" ? "light" : "dark"));
  });

  const activeSlug = root.dataset.activeChapter;
  document.querySelectorAll(`[data-slug="${CSS.escape(activeSlug)}"]`).forEach((link) => link.classList.add("active"));

  function updateProgress() {
    const chapterLinks = [...document.querySelectorAll(".chapter-link")];
    chapterLinks.forEach((link) => {
      link.classList.toggle("completed", completed.has(link.dataset.slug));
    });
    document.querySelectorAll("[data-chapter-card]").forEach((card) => {
      card.classList.toggle("completed", completed.has(card.dataset.chapterCard));
    });
    const done = chapterLinks.filter((link) => completed.has(link.dataset.slug)).length;
    const label = document.querySelector("#progress-label");
    const bar = document.querySelector("#progress-bar");
    if (label) label.textContent = `${done} з ${chapterLinks.length}`;
    if (bar) bar.style.width = chapterLinks.length ? `${(done / chapterLinks.length) * 100}%` : "0%";

    document.querySelectorAll(".complete-chapter").forEach((button) => {
      const isComplete = completed.has(button.dataset.chapterId);
      button.textContent = isComplete ? "Завершено ✓" : "Позначити завершеним";
      button.closest(".completion-card")?.classList.toggle("completed", isComplete);
    });
  }

  document.querySelectorAll(".complete-chapter").forEach((button) => {
    button.addEventListener("click", () => {
      const chapterId = button.dataset.chapterId;
      if (completed.has(chapterId)) completed.delete(chapterId);
      else completed.add(chapterId);
      writeSet(PROGRESS_KEY, completed);
      updateProgress();
    });
  });
  updateProgress();

  document.querySelectorAll(".task-check").forEach((checkbox) => {
    checkbox.checked = checkedTasks.has(checkbox.dataset.taskId);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) checkedTasks.add(checkbox.dataset.taskId);
      else checkedTasks.delete(checkbox.dataset.taskId);
      writeSet(TASKS_KEY, checkedTasks);
    });
  });

  document.querySelectorAll(".copy-code").forEach((button) => {
    button.addEventListener("click", async () => {
      const code = button.closest(".code-block")?.querySelector("code")?.textContent || "";
      try {
        await navigator.clipboard.writeText(code);
        button.textContent = "Скопійовано";
        button.classList.add("copied");
        window.setTimeout(() => {
          button.textContent = "Копіювати";
          button.classList.remove("copied");
        }, 1600);
      } catch {
        button.textContent = "Не вдалося";
      }
    });
  });

  document.querySelectorAll(".quiz").forEach((quiz) => {
    const answer = Number(quiz.dataset.answer);
    const options = [...quiz.querySelectorAll(".quiz-option")];
    const feedback = quiz.querySelector(".quiz-feedback");
    options.forEach((option) => {
      option.addEventListener("click", () => {
        options.forEach((item, index) => {
          item.disabled = true;
          item.classList.toggle("correct", index === answer);
        });
        if (Number(option.dataset.index) !== answer) option.classList.add("incorrect");
        if (feedback) {
          feedback.hidden = false;
          feedback.insertAdjacentText(
            "afterbegin",
            Number(option.dataset.index) === answer ? "Правильно. " : "Ще ні. "
          );
        }
      }, { once: true });
    });
  });

  const menuButton = document.querySelector(".menu-button");
  const closeMenu = () => {
    body.classList.remove("menu-open");
    menuButton?.setAttribute("aria-expanded", "false");
  };
  menuButton?.addEventListener("click", () => {
    const open = body.classList.toggle("menu-open");
    menuButton.setAttribute("aria-expanded", String(open));
  });
  document.querySelectorAll(".sidebar a").forEach((link) => link.addEventListener("click", closeMenu));
  document.addEventListener("click", (event) => {
    if (
      body.classList.contains("menu-open") &&
      !event.target.closest(".sidebar") &&
      !event.target.closest(".menu-button")
    ) closeMenu();
  });

  const searchInput = document.querySelector("#chapter-search");
  const searchPanel = document.querySelector(".search-panel");
  const searchResults = document.querySelector("#search-results");
  let searchIndexPromise;

  const getSearchIndex = () => {
    searchIndexPromise ||= fetch("search-index.json").then((response) => {
      if (!response.ok) throw new Error("Не вдалося завантажити індекс");
      return response.json();
    });
    return searchIndexPromise;
  };

  const escapeHtml = (value) => value.replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  }[char]));

  async function runSearch(query) {
    const normalized = query.trim().toLocaleLowerCase("uk");
    if (normalized.length < 2) {
      if (searchPanel) searchPanel.hidden = true;
      return;
    }
    if (searchPanel) searchPanel.hidden = false;
    if (searchResults) searchResults.innerHTML = "<p>Шукаю…</p>";
    try {
      const index = await getSearchIndex();
      const words = normalized.split(/\s+/).filter(Boolean);
      const matches = index
        .map((item) => {
          const haystack = `${item.title} ${item.text}`.toLocaleLowerCase("uk");
          const score = words.reduce((total, word) => total + (haystack.includes(word) ? 1 : 0), 0);
          const firstIndex = haystack.indexOf(words[0]);
          return { ...item, score, firstIndex };
        })
        .filter((item) => item.score === words.length)
        .sort((a, b) => b.score - a.score || a.firstIndex - b.firstIndex)
        .slice(0, 12);

      if (!searchResults) return;
      if (!matches.length) {
        searchResults.innerHTML = "<p>Нічого не знайдено. Спробуй коротше слово або іншу форму.</p>";
        return;
      }
      searchResults.innerHTML = matches.map((item) => {
        const start = Math.max(0, item.firstIndex - 70);
        const excerpt = item.text.slice(start, start + 210);
        return `<a class="search-result" href="${encodeURI(item.url)}"><strong>${escapeHtml(item.title)}</strong><span>…${escapeHtml(excerpt)}…</span></a>`;
      }).join("");
    } catch {
      if (searchResults) searchResults.innerHTML = "<p>Пошук тимчасово недоступний.</p>";
    }
  }

  searchInput?.addEventListener("input", () => runSearch(searchInput.value));
  document.querySelector(".search-close")?.addEventListener("click", () => {
    if (searchPanel) searchPanel.hidden = true;
    searchInput?.focus();
  });

  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLocaleLowerCase() === "k") {
      event.preventDefault();
      searchInput?.focus();
      body.classList.add("menu-open");
    }
    if (event.key === "Escape") {
      if (searchPanel) searchPanel.hidden = true;
      closeMenu();
    }
  });

  function updateReadingProgress() {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const progress = max > 0 ? Math.min(100, Math.max(0, (window.scrollY / max) * 100)) : 0;
    root.style.setProperty("--reading-progress", `${progress}%`);
  }
  updateReadingProgress();
  window.addEventListener("scroll", updateReadingProgress, { passive: true });
})();
