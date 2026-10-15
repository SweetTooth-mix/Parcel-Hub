import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { setTimeout as delay } from "node:timers/promises";
import { Window } from "happy-dom";

const source = await readFile("app/static/motion.js", "utf8");

function setup({
  reduced = false,
  intersection = true,
  animations = true,
} = {}) {
  const window = new Window();
  const media = new window.EventTarget();
  media.matches = reduced;
  window.matchMedia = () => media;
  const records = [];
  if (animations)
    window.Element.prototype.animate = function (frames, options) {
      let resolve, reject;
      const finished = new Promise((yes, no) => {
        resolve = yes;
        reject = no;
      });
      const animation = {
        effect: { target: this },
        frames,
        options,
        finished,
        cancelled: false,
        finish() {
          resolve();
        },
        cancel() {
          this.cancelled = true;
          reject(new Error("cancelled"));
        },
      };
      records.push(animation);
      return animation;
    };
  else window.Element.prototype.animate = undefined;
  let observer;
  window.IntersectionObserver = intersection
    ? class {
        targets = new Set();
        constructor(callback) {
          this.callback = callback;
          observer = this;
        }
        observe(element) {
          this.targets.add(element);
        }
        unobserve(element) {
          this.targets.delete(element);
        }
        disconnect() {
          this.targets.clear();
        }
        enter(element) {
          this.callback([{ target: element, isIntersecting: true }]);
        }
      }
    : undefined;
  window.eval(source);
  return {
    window,
    doc: window.document,
    media,
    records,
    observer,
    motion: window.ParcelHubMotion,
  };
}

test("Scroll entrances preserve readable headings, run once and release removed cards", async () => {
  const { window, doc, records, observer, motion } = setup();
  try {
    doc.body.innerHTML =
      '<div class="page-head"><h1>Parcel sampai.<br>Ambil <em>ikut masa.</em></h1></div><article class="panel"><p>RM 0.50</p></article>';
    const title = doc.querySelector("h1");
    const head = doc.querySelector(".page-head");
    const originalText = title.textContent;
    const card = doc.querySelector(".panel");
    motion.reveal(doc.body);
    assert.equal(records.length, 0, "Offscreen content waits for intersection");
    assert.equal(
      card.style.opacity,
      "",
      "Content never depends on a hidden CSS state",
    );
    observer.enter(head);
    assert.equal(title.textContent, originalText);
    assert.equal(title.querySelectorAll("br").length, 1);
    assert.equal(title.querySelector("em").textContent, "ikut masa.");
    assert.ok(
      records.some((item) => item.effect.target.className === "motion-word"),
    );
    const started = records.length;
    motion.reveal(doc.body);
    assert.equal(records.length, started);
    assert.equal(observer.targets.has(head), false);
    card.remove();
    motion.reveal(doc.body);
    assert.equal(
      observer.targets.size,
      0,
      "Removed pages are no longer observed",
    );
    doc.body.innerHTML = '<section class="panel"><h2>Fresh data</h2></section>';
    motion.withoutEntrance(() => motion.reveal(doc.body));
    assert.equal(
      observer.targets.size,
      0,
      "Background updates do not replay entrances",
    );
    assert.equal(records.length, started);
  } finally {
    await window.happyDOM.close();
  }
});

test("Reduced motion cancels running effects and keyboard focus stays immediately readable", async () => {
  const { window, doc, records, observer, motion, media } = setup();
  try {
    doc.body.innerHTML =
      '<section class="panel"><button>Ambil parcel</button></section><div class="stat">2 parcel</div>';
    const panel = doc.querySelector(".panel");
    const button = doc.querySelector("button");
    button.focus();
    motion.reveal(doc.body);
    observer.enter(panel);
    assert.equal(records.length, 0, "Focused controls are never faded out");
    observer.enter(doc.querySelector(".stat"));
    assert.equal(records.length, 1);
    const lateFocus = doc.createElement("button");
    doc.querySelector(".stat").append(lateFocus);
    lateFocus.focus();
    assert.equal(
      records[0].cancelled,
      true,
      "Tabbing into an entering card immediately restores visibility",
    );
    doc.body.insertAdjacentHTML(
      "beforeend",
      '<div class="stat">3 parcel</div>',
    );
    motion.reveal(doc.body);
    observer.enter(doc.querySelector(".stat:last-child"));
    assert.equal(records.length, 2);
    media.matches = true;
    media.dispatchEvent(new window.Event("change"));
    assert.ok(records.every((animation) => animation.cancelled));
    assert.equal(observer.targets.size, 0);
    doc.body.innerHTML = '<div class="page-head"><h1>Semua parcel.</h1></div>';
    motion.reveal(doc.body);
    assert.equal(doc.querySelector("h1").textContent, "Semua parcel.");
    assert.equal(doc.querySelector(".motion-word"), null);
    assert.equal(records.length, 2);
  } finally {
    await window.happyDOM.close();
  }
});

test("Missing animation APIs keep the UI usable; busy state always clears", async () => {
  const { window, doc, records, motion } = setup({
    intersection: false,
    animations: false,
  });
  try {
    doc.body.innerHTML =
      '<div class="page-head"><h1>Parcel saya.</h1></div><button>Hantar mesej ujian</button>';
    motion.reveal(doc.body);
    assert.equal(doc.querySelector("h1").textContent, "Parcel saya.");
    assert.equal(records.length, 0);
    const button = doc.querySelector("button");
    const done = motion.busy(button);
    await delay(180);
    assert.equal(button.getAttribute("aria-busy"), "true");
    assert.equal(button.textContent, "Hantar mesej ujian");
    assert.ok(button.classList.contains("is-loading"));
    done();
    assert.equal(button.hasAttribute("aria-busy"), false);
    assert.equal(button.classList.contains("is-loading"), false);
    const immediate = motion.busy(button);
    immediate();
    await delay(180);
    assert.equal(button.classList.contains("is-loading"), false);
  } finally {
    await window.happyDOM.close();
  }
});

test("Keyboard clicks receive a disposable ripple without changing the button label", async () => {
  const { window, doc, records, motion } = setup({ intersection: false });
  try {
    doc.body.innerHTML =
      '<div class="page-head"><h1>Parcel saya.</h1></div><button>Buka loker</button>';
    motion.reveal(doc.body);
    assert.ok(
      records.length > 0,
      "Entrances also work without IntersectionObserver",
    );
    const button = doc.querySelector("button");
    button.getBoundingClientRect = () => ({
      width: 100,
      height: 40,
      left: 10,
      top: 10,
    });
    button.click();
    assert.equal(button.textContent, "Buka loker");
    const ripple = button.querySelector(".click-ripple");
    assert.equal(ripple.getAttribute("aria-hidden"), "true");
    records.at(-1).finish();
    await Promise.resolve();
    assert.equal(button.querySelector(".click-ripple"), null);
    button.disabled = true;
    button.click();
    assert.equal(button.querySelector(".click-ripple"), null);
  } finally {
    await window.happyDOM.close();
  }
});
