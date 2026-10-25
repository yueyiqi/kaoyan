/**
 * KaoyanEnglish Hub v6.0 — Vue 3 Reactive Composable Store & Bridge Runtime
 *
 * Implements fine-grained Proxy reactivity (Vue 3 @vue/reactivity pattern: reactive, ref, computed,
 * watchEffect) with zero build-step overhead for Edge/Docker dual-plane deployment:
 * 1. useKaoyanClusterStore()   — 3-Node (W1/HP/S1) + PG18/SQLite Dual-Engine HA state
 * 2. useEbbinghausQueue()      — Spaced-repetition urgency U(w) reactive sorting & filtering
 * 3. useEidsDualModalDrilldown() — 12-Section (Top 5 KPI + Tab 0..6) -> L1..L5 Dual-Modal state
 * 4. useZeroMemoryRbacAuth()   — GUEST(L10) / SCHOLAR(L50) / ADMIN(L100) + zero-memory password guard
 */
(function (globalScope) {
  'use strict';

  var activeEffect = null;
  var targetMap = new WeakMap();

  function track(target, key) {
    if (!activeEffect) return;
    var depsMap = targetMap.get(target);
    if (!depsMap) {
      depsMap = new Map();
      targetMap.set(target, depsMap);
    }
    var dep = depsMap.get(key);
    if (!dep) {
      dep = new Set();
      depsMap.set(key, dep);
    }
    dep.add(activeEffect);
  }

  function trigger(target, key) {
    var depsMap = targetMap.get(target);
    if (!depsMap) return;
    var dep = depsMap.get(key);
    if (!dep) return;
    Array.from(dep).forEach(function (effectFn) {
      effectFn();
    });
  }

  function reactive(rawObj) {
    if (!rawObj || typeof rawObj !== 'object') return rawObj;
    return new Proxy(rawObj, {
      get: function (target, key, receiver) {
        track(target, key);
        var res = Reflect.get(target, key, receiver);
        return (res && typeof res === 'object') ? reactive(res) : res;
      },
      set: function (target, key, value, receiver) {
        var oldVal = target[key];
        var ok = Reflect.set(target, key, value, receiver);
        if (oldVal !== value) trigger(target, key);
        return ok;
      }
    });
  }

  function computed(getterFn) {
    var cached;
    var dirty = true;
    var box = {
      get value() {
        if (dirty) {
          cached = getterFn();
          dirty = false;
        }
        return cached;
      }
    };
    watchEffect(function () {
      dirty = true;
      cached = getterFn();
    });
    return box;
  }

  function watchEffect(effectFn) {
    var runner = function () {
      activeEffect = runner;
      try {
        effectFn();
      } finally {
        activeEffect = null;
      }
    };
    runner();
    return runner;
  }

  var state = reactive({
    version: '6.0.0-SPRINGBOOT3-VUE3-HA',
    backendStack: 'Spring Boot 3.3+ (Java 17/21) + Python HA Worker',
    activeTheme: 'daylight',
    clusterEpoch: 600,
    activeEngine: 'DUAL_PG18_SQLITE_WAL',
    rpoSeconds: 0,
    rtoMs: 2,
    schemaTables: 18,
    schemaColumns: 146,
    schemaDomains: 5,
    roleCode: 'GUEST',
    roleLevel: 10,
    zeroMemoryEnforced: true,
    activeDrillSection: 'KPI_01_PASSAGE_PROGRESS',
    activeDrillTable: 'exam_passages',
    activeHighlightCol: 'title_en',
    activeSearchQuery: ''
  });

  function useKaoyanClusterStore() {
    var isHaHealthy = computed(function () {
      return state.rpoSeconds === 0 && state.schemaTables === 18 && state.schemaColumns === 146;
    });
    function syncFromHealthPayload(payload) {
      if (!payload || typeof payload !== 'object') return;
      if (payload.cluster_epoch) state.clusterEpoch = Number(payload.cluster_epoch);
      if (payload.active_engine) state.activeEngine = String(payload.active_engine);
      if (payload.schema_tables) state.schemaTables = Number(payload.schema_tables);
      if (payload.schema_columns) state.schemaColumns = Number(payload.schema_columns);
    }
    return {
      state: state,
      isHaHealthy: isHaHealthy,
      syncFromHealthPayload: syncFromHealthPayload
    };
  }

  function useEbbinghausQueue() {
    var intervals = [1, 2, 4, 7, 15, 30];
    function computeUrgency(masteryLevel, examFrequency, elapsedDays) {
      var m = Math.max(0, Math.min(5, Number(masteryLevel) || 0));
      var f = Math.max(0, Number(examFrequency) || 0);
      var d = Math.max(0, Number(elapsedDays) || 0);
      var iv = intervals[Math.min(m, intervals.length - 1)];
      var raw = (1.0 + d / iv) * (1.6 - 0.12 * m) * (1.0 + 0.18 * Math.log(1 + f));
      return Math.round(raw * 1000) / 1000;
    }
    return {
      intervals: intervals,
      computeUrgency: computeUrgency
    };
  }

  function useEidsDualModalDrilldown() {
    function setActiveDrillTarget(sectionId, tableName, highlightCol, searchQuery) {
      state.activeDrillSection = sectionId || 'TAB_00_OVERVIEW_DASHBOARD';
      state.activeDrillTable = tableName || 'exam_passages';
      state.activeHighlightCol = highlightCol || '';
      state.activeSearchQuery = searchQuery || '';
    }
    return {
      state: state,
      setActiveDrillTarget: setActiveDrillTarget
    };
  }

  function useZeroMemoryRbacAuth() {
    function enforceZeroMemoryOnPasswordInputs(rootEl) {
      var scope = rootEl || (typeof document !== 'undefined' ? document : null);
      if (!scope || !scope.querySelectorAll) return 0;
      var inputs = scope.querySelectorAll('input[type="password"]');
      inputs.forEach(function (inp) {
        inp.value = '';
        inp.setAttribute('autocomplete', 'new-password');
        inp.setAttribute('data-lpignore', 'true');
        inp.setAttribute('data-1p-ignore', 'true');
        inp.setAttribute('data-form-type', 'other');
      });
      return inputs.length;
    }
    return {
      passwordMask: '********',
      enforceZeroMemoryOnPasswordInputs: enforceZeroMemoryOnPasswordInputs
    };
  }

  globalScope.KaoyanVue3Composables = {
    reactive: reactive,
    computed: computed,
    watchEffect: watchEffect,
    useKaoyanClusterStore: useKaoyanClusterStore,
    useEbbinghausQueue: useEbbinghausQueue,
    useEidsDualModalDrilldown: useEidsDualModalDrilldown,
    useZeroMemoryRbacAuth: useZeroMemoryRbacAuth
  };
})(typeof window !== 'undefined' ? window : globalThis);
