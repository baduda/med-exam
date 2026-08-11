"use strict";

const KEY = "med-exam-progress";
const BOOKS_KEY = "med-exam-books";
const LETTERS = ["A", "B", "C", "D", "E"];
const el = (id) => document.getElementById(id);

// Display order and Polish labels for source.book values (see pipeline/books.py).
const BOOKS = [
  ["Tom1", "Rahnama, tom 1"],
  ["Tom2", "Rahnama, tom 2"],
  ["Tom3", "Rahnama, tom 3"],
  ["Janczuk", "Jańczuk — stomatologia zachowawcza"],
  ["Arabska", "Arabska-Przedpełska — endodoncja"],
];

let questions = [];
let queue = [];
let idx = 0;
let answered = 0;
let correct = 0;

const loadProgress = () =>
  JSON.parse(localStorage.getItem(KEY) || '{"done":[],"correct":0,"answered":0}');
const saveProgress = (s) => localStorage.setItem(KEY, JSON.stringify(s));

function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const bookBoxes = () => [...el("books").querySelectorAll("input")];
const selectedBooks = () =>
  new Set(bookBoxes().filter((b) => b.checked).map((b) => b.value));

function renderBooks() {
  const present = BOOKS.filter(([book]) =>
    questions.some((q) => q.source.book === book));
  const saved = JSON.parse(localStorage.getItem(BOOKS_KEY) || "null");
  el("books").innerHTML = "";
  for (const [book, label] of present) {
    const count = questions.filter((q) => q.source.book === book).length;
    const id = `book-${book}`;
    const wrap = document.createElement("label");
    wrap.className = "check";
    wrap.htmlFor = id;
    const box = document.createElement("input");
    box.type = "checkbox";
    box.id = id;
    box.value = book;
    box.checked = saved ? saved.includes(book) : true;
    box.onchange = onBooksChange;
    wrap.append(box, document.createTextNode(`${label} (${count})`));
    el("books").appendChild(wrap);
  }
  // A saved selection can leave nothing checked if a book later disappears.
  if (!selectedBooks().size) bookBoxes().forEach((b) => (b.checked = true));
}

function onBooksChange(e) {
  // Never let the user deselect everything — there would be nothing to practise.
  if (!selectedBooks().size) {
    e.target.checked = true;
    return;
  }
  localStorage.setItem(BOOKS_KEY, JSON.stringify([...selectedBooks()]));
  renderLoaded();
}

function pool() {
  const books = selectedBooks();
  return questions.filter(
    (q) => books.has(q.source.book) && (el("scope").value !== "core" || q.core));
}

function buildQueue() {
  const p = pool();
  return el("mode").value === "random" ? shuffle(p) : p;
}

function renderLoaded() {
  const n = pool().length;
  const scope = el("scope").value === "core" ? "Zakres kluczowy" : "Wszystkie pytania";
  el("loaded").textContent = `${scope}: ${n} pytań (z ${questions.length})`;
  el("start-btn").disabled = n === 0;
}

function renderScore() {
  el("score").textContent = `Wynik: ${correct}/${answered}`;
}

function renderQuestion() {
  el("explanation").hidden = true;
  el("source").hidden = true;
  el("next-btn").hidden = true;

  if (idx >= queue.length) {
    el("progress").textContent = "";
    el("bar-fill").style.width = "100%";
    el("question").textContent = "Koniec zestawu. Dobra robota! 🦷";
    el("options").innerHTML = "";
    return;
  }

  const q = queue[idx];
  el("bar-fill").style.width = `${(idx / queue.length) * 100}%`;
  el("progress").textContent = `Pytanie ${idx + 1} z ${queue.length}`;
  const badge = { combined: "Zestaw twierdzeń", clinical: "Przypadek kliniczny" }[q.type];
  el("qtype").textContent = badge || "";
  el("qtype").hidden = !badge;
  el("question").textContent = q.question;
  el("options").innerHTML = "";
  for (const k of LETTERS) {
    const li = document.createElement("li");
    li.textContent = `${k}. ${q.options[k]}`;
    li.dataset.key = k;
    li.onclick = () => choose(q, k, li);
    el("options").appendChild(li);
  }
}

function choose(q, k, li) {
  const items = [...el("options").children];
  items.forEach((c) => { c.onclick = null; c.classList.add("locked"); });
  items[LETTERS.indexOf(q.correct)].classList.add("correct");
  if (k !== q.correct) li.classList.add("wrong");

  answered++;
  if (k === q.correct) correct++;
  renderScore();

  el("explanation").textContent = q.explanation;
  el("explanation").hidden = false;
  if (q.source) {
    el("source").textContent =
      `Źródło: ${q.source.book}, s. ${q.source.pages.join("–")}`;
    el("source").hidden = false;
  }
  el("next-btn").hidden = false;
  // reveal explanation + Dalej without manual scrolling (esp. on mobile)
  el("next-btn").scrollIntoView({ behavior: "smooth", block: "center" });

  const s = loadProgress();
  s.answered = answered;
  s.correct = correct;
  if (!s.done.includes(q.id)) s.done.push(q.id);
  saveProgress(s);
}

el("scope").onchange = renderLoaded;
el("start-btn").onclick = () => {
  queue = buildQueue();
  idx = 0;
  el("start").hidden = true;
  el("quiz").hidden = false;
  renderQuestion();
};
el("next-btn").onclick = () => { idx++; renderQuestion(); };
el("reset-btn").onclick = () => {
  saveProgress({ done: [], correct: 0, answered: 0 });
  answered = 0;
  correct = 0;
  renderScore();
};

fetch("questions.json")
  .then((r) => r.json())
  .then((data) => {
    questions = data;
    const s = loadProgress();
    answered = s.answered;
    correct = s.correct;
    renderScore();
    renderBooks();
    renderLoaded();
  })
  .catch(() => {
    el("loaded").textContent = "Nie udało się wczytać pytań (questions.json).";
  });
