import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { readFile } from "node:fs/promises";
import { setTimeout as delay } from "node:timers/promises";
import { Window } from "happy-dom";

// DOM integration, not a visual browser test. The Python TestClient handles real
// server transactions and cookies without starting a preview or listening socket.
test(
  "Recipient pickup, operator deposit and admin navigation through real API",
  { timeout: 30000 },
  async () => {
    const py = spawn(
      process.env.PYTHON || ".venv/bin/python",
      ["-m", "tests.api_bridge"],
      { stdio: ["pipe", "pipe", "pipe"] },
    );
    const pending = new Map();
    let seq = 0;
    let stderr = "";
    py.stderr.on("data", (d) => (stderr += d.toString()));
    createInterface({ input: py.stdout }).on("line", (line) => {
      const data = JSON.parse(line);
      pending.get(data.id)?.(data);
      pending.delete(data.id);
    });
    const window = new Window({
      url: "http://testserver/",
      settings: {
        disableCSSFileLoading: true,
        disableJavaScriptFileLoading: true,
      },
    });
    window.HTMLDialogElement.prototype.showModal = function () {
      this.setAttribute("open", "");
    };
    window.HTMLDialogElement.prototype.close = function () {
      this.removeAttribute("open");
      this.dispatchEvent(new window.Event("close"));
    };
    window.fetch = async (url, options = {}) => {
      const id = ++seq;
      const response = new Promise((resolve) => pending.set(id, resolve));
      py.stdin.write(
        JSON.stringify({
          id,
          url,
          method: options.method || "GET",
          headers: options.headers || {},
          body: options.body,
        }) + "\n",
      );
      const result = await response;
      return new window.Response(JSON.stringify(result.body), {
        status: result.status,
        headers: { "content-type": "application/json" },
      });
    };
    const doc = window.document;
    const wait = async (fn, msg) => {
      for (let i = 0; i < 150; i++) {
        if (fn()) return;
        await delay(20);
      }
      throw new Error(msg + "\n" + doc.body.innerText + "\n" + stderr);
    };
    const click = async (selector) => {
      await wait(() => doc.querySelector(selector), "Missing " + selector);
      doc.querySelector(selector).click();
      await delay(50);
    };
    const submit = (selector) =>
      doc
        .querySelector(selector)
        .dispatchEvent(
          new window.Event("submit", { bubbles: true, cancelable: true }),
        );
    try {
      doc.write(await readFile("app/static/index.html", "utf8"));
      window.eval(await readFile("app/static/app.js", "utf8"));
      await click('[data-action="demo-login"][data-role="recipient"]');
      await wait(
        () => doc.querySelector("h1")?.textContent.includes("Aiman"),
        "Recipient dashboard did not load",
      );
      assert.equal(doc.querySelectorAll(".parcel-card").length, 2);
      await click('[data-action="code"][data-id="PH-DEMO01"]');
      await wait(
        () => doc.querySelector(".code-display"),
        "Pickup code did not appear",
      );
      assert.match(doc.querySelector(".code-display").textContent, /^\d{6}$/);
      assert.ok(
        doc
          .querySelector(".qr-box img")
          .getAttribute("src")
          .startsWith("data:image/svg+xml"),
      );
      await click('[data-action="use-code"]');
      await wait(
        () => doc.querySelector('[data-action="kiosk-pay"]'),
        "Kiosk fee step missing",
      );
      await click('[data-action="kiosk-pay"]');
      await click('[data-action="kiosk-unlock"]');
      await wait(
        () =>
          doc
            .querySelector('.locker-box[data-bay="A02"]')
            .classList.contains("open"),
        "Door did not animate to open state",
      );
      await click('[data-action="kiosk-close"][data-present="false"]');
      await wait(() => doc.querySelector(".kiosk-success"), "Receipt missing");
      assert.match(doc.querySelector(".kiosk-success").textContent, /RM 0.50/);
      await click('[data-action="nav"][data-view="parcels"]');
      await click('[data-action="filter-tab"][data-tab="history"]');
      await wait(
        () =>
          doc
            .querySelector(".parcel-card")
            ?.textContent.includes("Selesai diambil"),
        "History missing",
      );
      await click('[data-action="account"]');
      await click('[data-action="logout"]');
      await click('[data-action="demo-login"][data-role="operator"]');
      await click('[data-action="nav"][data-view="deposit"]');
      await wait(
        () => doc.querySelector("#deposit-form"),
        "Deposit form missing",
      );
      doc.querySelector("#recipient").value = "1";
      doc.querySelector('[name="tracking"]').value = "UIFLOW100";
      submit("#deposit-form");
      await wait(
        () => doc.querySelector('[data-action="deposit-close"]'),
        "Deposit confirmation missing",
      );
      await click('[data-action="deposit-close"][data-present="true"]');
      await wait(
        () => !doc.querySelector("#modal").open,
        "Deposit did not finish",
      );
      await click('[data-action="nav"][data-view="parcels"]');
      await wait(() => doc.querySelector("#parcel-search"), "Search missing");
      doc.querySelector("#parcel-search").value = "UIFLOW100";
      doc
        .querySelector("#parcel-search")
        .dispatchEvent(new window.Event("input", { bubbles: true }));
      assert.equal(doc.querySelectorAll("tbody tr").length, 1);
      assert.match(doc.querySelector("tbody").textContent, /Sedia diambil/);
      await click('[data-action="account"]');
      await click('[data-action="logout"]');
      await click('[data-action="demo-login"][data-role="admin"]');
      await click('[data-action="nav"][data-view="users"]');
      await wait(
        () => doc.querySelector('[data-action="new-user"]'),
        "Admin users missing",
      );
      assert.equal(doc.querySelectorAll("tbody tr").length, 5);
      await click('[data-action="nav"][data-view="lockers"]');
      await wait(
        () => doc.querySelectorAll(".locker-tile").length === 16,
        "Locker layout missing",
      );
      await click('[data-action="locker-detail"][data-id="C04"]');
      assert.ok(doc.querySelector("#maintenance-form"));
    } finally {
      window.happyDOM.abort();
      await window.happyDOM.close();
      py.stdin.end();
      py.kill();
    }
  },
);
