try {
  self["workbox:window:7.2.0"] && _()
} catch {}
function E(n, r) {
  return new Promise((t) => {
    const i = new MessageChannel()
    ;(i.port1.onmessage = (c) => {
      t(c.data)
    }),
      n.postMessage(r, [i.port2])
  })
}
function W(n) {
  const r = ((t, i) => {
    if (typeof t !== "object" || !t) return t
    const c = t[Symbol.toPrimitive]
    if (c !== void 0) {
      const h = c.call(t, i)
      if (typeof h !== "object") return h
      throw new TypeError("@@toPrimitive must return a primitive value.")
    }
    return String(t)
  })(n, "string")
  return typeof r === "symbol" ? r : `${r}`
}
function k(n, r) {
  for (let t = 0; t < r.length; t++) {
    const i = r[t]
    ;(i.enumerable = i.enumerable || !1),
      (i.configurable = !0),
      "value" in i && (i.writable = !0),
      Object.defineProperty(n, W(i.key), i)
  }
}
function P(n, r) {
  return (
    (P = Object.setPrototypeOf
      ? Object.setPrototypeOf.bind()
      : (t, i) => ((t.__proto__ = i), t)),
    P(n, r)
  )
}
function j(n, r) {
  ;(r == null || r > n.length) && (r = n.length)
  for (let t = 0, i = new Array(r); t < r; t++) i[t] = n[t]
  return i
}
function L(n, r) {
  let t = (typeof Symbol < "u" && n[Symbol.iterator]) || n["@@iterator"]
  if (t) return (t = t.call(n)).next.bind(t)
  if (
    Array.isArray(n) ||
    (t = ((c, h) => {
      if (c) {
        if (typeof c === "string") return j(c, h)
        let l = Object.prototype.toString.call(c).slice(8, -1)
        return (
          l === "Object" && c.constructor && (l = c.constructor.name),
          l === "Map" || l === "Set"
            ? Array.from(c)
            : l === "Arguments" ||
                /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(l)
              ? j(c, h)
              : void 0
        )
      }
    })(n)) ||
    r
  ) {
    t && (n = t)
    let i = 0
    return () => (i >= n.length ? { done: !0 } : { done: !1, value: n[i++] })
  }
  throw new TypeError(`Invalid attempt to iterate non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)
}
try {
  self["workbox:core:7.2.0"] && _()
} catch {}
const w = function () {
  this.promise = new Promise((r, t) => {
    ;(this.resolve = r), (this.reject = t)
  })
}
function b(n, r) {
  const t = location.href
  return new URL(n, t).href === new URL(r, t).href
}
const g = function (n, r) {
  ;(this.type = n), Object.assign(this, r)
}
function d(n, r, t) {
  return t
    ? r
      ? r(n)
      : n
    : (n?.then || (n = Promise.resolve(n)), r ? n.then(r) : n)
}
function O() {}
const x = { type: "SKIP_WAITING" }
function S(n, r) {
  return n?.then ? n.then(O) : Promise.resolve()
}
const U = ((n) => {
  function r(v, u) {
    let e
    let o
    return (
      u === void 0 && (u = {}),
      ((e = n.call(this) || this).nn = {}),
      (e.tn = 0),
      (e.rn = new w()),
      (e.en = new w()),
      (e.on = new w()),
      (e.un = 0),
      (e.an = new Set()),
      (e.cn = () => {
        const s = e.fn
        const a = s.installing
        e.tn > 0 ||
        !b(a.scriptURL, e.sn.toString()) ||
        performance.now() > e.un + 6e4
          ? ((e.vn = a), s.removeEventListener("updatefound", e.cn))
          : ((e.hn = a), e.an.add(a), e.rn.resolve(a)),
          ++e.tn,
          a.addEventListener("statechange", e.ln)
      }),
      (e.ln = (s) => {
        const a = e.fn
        const f = s.target
        const p = f.state
        const m = f === e.vn
        const y = { sw: f, isExternal: m, originalEvent: s }
        !m && e.mn && (y.isUpdate = !0),
          e.dispatchEvent(new g(p, y)),
          p === "installed"
            ? (e.wn = self.setTimeout(() => {
                p === "installed" &&
                  a.waiting === f &&
                  e.dispatchEvent(new g("waiting", y))
              }, 200))
            : p === "activating" && (clearTimeout(e.wn), m || e.en.resolve(f))
      }),
      (e.yn = (s) => {
        const a = e.hn
        const f = a !== navigator.serviceWorker.controller
        e.dispatchEvent(
          new g("controlling", {
            isExternal: f,
            originalEvent: s,
            sw: a,
            isUpdate: e.mn,
          }),
        ),
          f || e.on.resolve(a)
      }),
      (e.gn =
        ((o = (s) => {
          const a = s.data
          const f = s.ports
          const p = s.source
          return d(e.getSW(), () => {
            e.an.has(p) &&
              e.dispatchEvent(
                new g("message", {
                  data: a,
                  originalEvent: s,
                  ports: f,
                  sw: p,
                }),
              )
          })
        }),
        function () {
          for (let s = [], a = 0; a < arguments.length; a++) s[a] = arguments[a]
          try {
            return Promise.resolve(o.apply(this, s))
          } catch (f) {
            return Promise.reject(f)
          }
        })),
      (e.sn = v),
      (e.nn = u),
      navigator.serviceWorker.addEventListener("message", e.gn),
      e
    )
  }
  let t
  let i
  ;(i = n),
    ((t = r).prototype = Object.create(i.prototype)),
    (t.prototype.constructor = t),
    P(t, i)
  let c
  let h
  const l = r.prototype
  return (
    (l.register = function (v) {
      const u = (v === void 0 ? {} : v).immediate
      const e = u !== void 0 && u
      try {
        return d(
          ((s, a) => {
            const f = s()
            return f?.then ? f.then(a) : a(f)
          })(
            () => {
              if (!e && document.readyState !== "complete")
                return S(new Promise((s) => window.addEventListener("load", s)))
            },
            () => (
              (this.mn = !!navigator.serviceWorker.controller),
              (this.dn = this.pn()),
              d(this.bn(), (s) => {
                ;(this.fn = s),
                  this.dn &&
                    ((this.hn = this.dn),
                    this.en.resolve(this.dn),
                    this.on.resolve(this.dn),
                    this.dn.addEventListener("statechange", this.ln, {
                      once: !0,
                    }))
                const a = this.fn.waiting
                return (
                  a &&
                    b(a.scriptURL, this.sn.toString()) &&
                    ((this.hn = a),
                    Promise.resolve()
                      .then(() => {
                        this.dispatchEvent(
                          new g("waiting", {
                            sw: a,
                            wasWaitingBeforeRegister: !0,
                          }),
                        )
                      })
                      .then(() => {})),
                  this.hn && (this.rn.resolve(this.hn), this.an.add(this.hn)),
                  this.fn.addEventListener("updatefound", this.cn),
                  navigator.serviceWorker.addEventListener(
                    "controllerchange",
                    this.yn,
                  ),
                  this.fn
                )
              })
            ),
          ),
        )
      } catch (s) {
        return Promise.reject(s)
      }
    }),
    (l.update = function () {
      try {
        return this.fn ? d(S(this.fn.update())) : d()
      } catch (v) {
        return Promise.reject(v)
      }
    }),
    (l.getSW = function () {
      return this.hn !== void 0 ? Promise.resolve(this.hn) : this.rn.promise
    }),
    (l.messageSW = function (v) {
      try {
        return d(this.getSW(), (u) => E(u, v))
      } catch (u) {
        return Promise.reject(u)
      }
    }),
    (l.messageSkipWaiting = function () {
      this.fn?.waiting && E(this.fn.waiting, x)
    }),
    (l.pn = function () {
      const v = navigator.serviceWorker.controller
      return v && b(v.scriptURL, this.sn.toString()) ? v : void 0
    }),
    (l.bn = function () {
      try {
        return d(
          ((u, e) => {
            try {
              const o = u()
            } catch (s) {
              return e(s)
            }
            return o?.then ? o.then(void 0, e) : o
          })(
            () =>
              d(
                navigator.serviceWorker.register(this.sn, this.nn),
                (u) => ((this.un = performance.now()), u),
              ),
            (u) => {
              throw u
            },
          ),
        )
      } catch (u) {
        return Promise.reject(u)
      }
    }),
    (c = r),
    (h = [
      {
        key: "active",
        get: function () {
          return this.en.promise
        },
      },
      {
        key: "controlling",
        get: function () {
          return this.on.promise
        },
      },
    ]) && k(c.prototype, h),
    Object.defineProperty(c, "prototype", { writable: !1 }),
    c
  )
})(
  (() => {
    function n() {
      this.Pn = new Map()
    }
    const r = n.prototype
    return (
      (r.addEventListener = function (t, i) {
        this.jn(t).add(i)
      }),
      (r.removeEventListener = function (t, i) {
        this.jn(t).delete(i)
      }),
      (r.dispatchEvent = function (t) {
        t.target = this
        for (let i, c = L(this.jn(t.type)); !(i = c()).done; ) (0, i.value)(t)
      }),
      (r.jn = function (t) {
        return this.Pn.has(t) || this.Pn.set(t, new Set()), this.Pn.get(t)
      }),
      n
    )
  })(),
)
export { U as Workbox, g as WorkboxEvent, E as messageSW }
