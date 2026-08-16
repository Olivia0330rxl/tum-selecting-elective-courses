(() => {
  "use strict";

  const PALETTE = ["#007C91", "#D97706", "#7C3AED", "#15803D", "#C2416C", "#2563EB", "#A13D2D", "#52796F"];
  const DAY_START_MINUTES = 8 * 60;
  const PIXELS_PER_MINUTE = 0.9;
  const SENSITIVE_KEY = /password|passwd|credential|secret|token|cookie|session.?id|otp|mfa|student.?id|matriculation|matrikel|email|grade|exam.?result|first.?name|last.?name|full.?name|account.?id|raw.?(html|dom|page)/i;
  const TEXT = {
    en: {
      eyebrow: "TUM ELECTIVE PLANNER · LOCAL ONLY", import: "Import JSON", export: "Export JSON", print: "Print",
      planning: "Planning", requirementsKicker: "CURRICULUM REQUIREMENTS", progressTitle: "Credit progress",
      coursesKicker: "NEXT-SEMESTER OFFERINGS", coursesTitle: "Choose courses", searchLabel: "Search courses",
      searchPlaceholder: "Search title or module code", categoryLabel: "Filter category", calendarKicker: "WEEKLY VIEW",
      calendarTitle: "Your timetable", evidenceKicker: "TRACEABILITY", evidenceTitle: "Sources and limitations",
      disclaimer: "Personal, non-commercial planning support only. Information may be incomplete or incorrect; TUMonline is authoritative.", localOnly: "This file works offline and sends no data.",
      allCategories: "All categories", unclassified: "Unclassified", add: "Add", remove: "Remove", enrolled: "Enrolled",
      planned: "planned", courses: "courses", creditsPlanned: "ECTS planned", minimum: "minimum", maximum: "maximum",
      noRequirement: "No numeric requirement", remaining: "remaining", complete: "requirement met", noCourses: "No matching courses.",
      unavailable: "Next-semester offerings have not been published. No current-semester courses were substituted.",
      partial: "Only part of the next-semester catalogue is currently available.", conflicts: "conflicts", noConflicts: "No conflicts",
      timeTba: "Time to be announced", noTime: "Selected courses without a published time", chooseGroup: "Choose section",
      generated: "Generated", fromCurrent: "from current", overridden: "User-selected target term", importError: "Could not import this file",
      imported: "Imported locally. Nothing was uploaded.", sourceConflict: "Source conflict", observed: "Observed",
      source: "Source", ectsUnknown: "ECTS unknown", category: "Category", selected: "Selected", statusCandidate: "Candidate",
      selectVisible: "Select visible", clearVisible: "Deselect visible", tracks: "Tracks", allTracks: "All tracks",
      fontSize: "Font size", calendarWidth: "Calendar width", scheduleUnverified: "Schedule not checked",
      registrationOpen: "Registration open", registrationUpcoming: "Registration upcoming", registrationNone: "No registration procedure",
      registrationUnknown: "Registration status unknown", noTimePublished: "Published without a meeting time", detailPending: "Detail verification pending", scheduledCourses: "Scheduled courses"
    },
    zh: {
      eyebrow: "TUM 选课规划 · 仅本地运行", import: "导入 JSON", export: "导出 JSON", print: "打印",
      planning: "正在规划", requirementsKicker: "培养方案要求", progressTitle: "分类学分进度",
      coursesKicker: "下一学期课程", coursesTitle: "选择课程", searchLabel: "搜索课程",
      searchPlaceholder: "搜索课程名或模块编号", categoryLabel: "按大类筛选", calendarKicker: "周视图",
      calendarTitle: "你的课表", evidenceKicker: "可追溯性", evidenceTitle: "来源与限制",
      disclaimer: "仅限个人、非商业选课规划使用。信息可能不完整或有误，一切以 TUMonline 为准。", localOnly: "此文件可离线使用，不会发送数据。",
      allCategories: "全部大类", unclassified: "待分类", add: "加入", remove: "移除", enrolled: "已报名",
      planned: "已规划", courses: "门课程", creditsPlanned: "已规划 ECTS", minimum: "最低", maximum: "最高",
      noRequirement: "没有数值学分要求", remaining: "仍需", complete: "已满足要求", noCourses: "没有符合筛选条件的课程。",
      unavailable: "下一学期课程尚未发布；没有使用当前学期课程替代。", partial: "下一学期课程目前只发布了一部分。",
      conflicts: "处冲突", noConflicts: "无冲突", timeTba: "时间待公布", noTime: "以下已选课程尚未公布时间",
      chooseGroup: "选择教学班", generated: "生成时间", fromCurrent: "基于当前学期", overridden: "用户指定目标学期",
      importError: "无法导入此文件", imported: "已在本地导入，没有上传任何数据。", sourceConflict: "来源冲突",
      observed: "读取时间", source: "来源", ectsUnknown: "ECTS 未知", category: "大类", selected: "已选择", statusCandidate: "候选"
      , selectVisible: "选择当前筛选结果", clearVisible: "反选当前筛选结果", tracks: "方向筛选", allTracks: "全部方向",
      fontSize: "字体大小", calendarWidth: "周历宽度", scheduleUnverified: "课程详情待核验",
      registrationOpen: "报名已开放", registrationUpcoming: "报名即将开放", registrationNone: "无报名流程",
      registrationUnknown: "报名状态未知", noTimePublished: "已确认无固定时间", detailPending: "详情时间待核验", scheduledCourses: "已有时间的课程"
    }
  };

  let language = "en";
  let state = parseInitialData();
  let activeTrackIds = new Set();
  let transientNotice = null;

  function parseInitialData() {
    const parsed = JSON.parse(document.getElementById("planner-data").textContent);
    const cloned = typeof structuredClone === "function" ? structuredClone(parsed) : JSON.parse(JSON.stringify(parsed));
    if (cloned.default_selected !== false) {
      cloned.courses.forEach(course => {
        if (course.status === "candidate") course.status = "planned";
        if (course.status === "planned" && !course.selected_group_id && course.session_groups?.length) course.selected_group_id = course.session_groups[0].id;
      });
    }
    return cloned;
  }

  function t(key) { return TEXT[language][key] || key; }
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }
  function minutes(value) {
    const [hours, mins] = value.split(":").map(Number);
    return hours * 60 + mins;
  }
  function selectedCourses() { return state.courses.filter(course => course.status === "planned" || course.status === "enrolled"); }
  function categoryById(id) { return state.categories.find(category => category.id === id); }
  function colorFor(categoryId) {
    if (!categoryId) return "#7C8581";
    const index = state.categories.findIndex(category => category.id === categoryId);
    const category = state.categories[index];
    return category?.color || PALETTE[(index < 0 ? 0 : index) % PALETTE.length];
  }
  function selectedGroup(course) {
    if (!course.session_groups?.length) return null;
    return course.session_groups.find(group => group.id === course.selected_group_id) || course.session_groups[0];
  }
  function formatEcts(value) { return value === null || value === undefined ? t("ectsUnknown") : `${value} ECTS`; }
  function formatObserved(value) {
    const date = new Date(value);
    return Number.isNaN(date.valueOf()) ? value : date.toLocaleString(language === "zh" ? "zh-CN" : "en-GB");
  }

  function render() {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach(node => { node.textContent = t(node.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(node => { node.placeholder = t(node.dataset.i18nPlaceholder); });
    document.getElementById("language-button").textContent = language === "en" ? "中文" : "English";
    renderHeader();
    renderNotices();
    renderCategoryFilter();
    renderTrackFilters();
    renderCourses();
    renderCalendar();
    renderEvidence();
  }

  function renderHeader() {
    document.getElementById("program-title").textContent = state.program.name;
    const degree = state.program.degree ? ` · ${state.program.degree}` : "";
    const version = state.program.curriculum_version_id ? ` · Curriculum ${state.program.curriculum_version_id}` : "";
    document.getElementById("program-meta").textContent = `${degree}${version}`.replace(/^ · /, "");
    document.getElementById("target-term").textContent = state.planning_term.target.label;
    const current = state.planning_term.current?.label || state.planning_term.current?.code || "—";
    document.getElementById("term-derivation").textContent = state.planning_term.method === "user_override" ? t("overridden") : `${t("fromCurrent")} ${current}`;
    document.getElementById("generated-at").textContent = `${t("generated")}: ${formatObserved(state.generated_at)}`;
  }

  function renderNotices() {
    const region = document.getElementById("notice-region");
    region.replaceChildren();
    if (state.offerings_status === "unavailable") region.append(el("div", "notice notice--danger", state.offerings_message || t("unavailable")));
    if (state.offerings_status === "partial") region.append(el("div", "notice", state.offerings_message || t("partial")));
    (state.conflicts || []).forEach(conflict => region.append(el("div", "notice", `${t("sourceConflict")}: ${conflict.message}`)));
    if (transientNotice) region.append(el("div", transientNotice.error ? "notice notice--danger" : "notice", transientNotice.message));
  }

  function renderProgress() {
    const selected = selectedCourses();
    const total = selected.reduce((sum, course) => sum + (Number(course.ects) || 0), 0);
    document.getElementById("total-ects").textContent = `${total} ${t("creditsPlanned")}`;
    const grid = document.getElementById("progress-grid");
    grid.replaceChildren();
    state.categories.forEach(category => {
      const amount = selected.filter(course => course.category_id === category.id).reduce((sum, course) => sum + (Number(course.ects) || 0), 0);
      const target = category.min_ects;
      const progress = target ? Math.min(100, amount / target * 100) : (amount > 0 ? 100 : 0);
      const card = el("article", "progress-card");
      card.style.setProperty("--category-color", colorFor(category.id));
      const top = el("div", "progress-card__top");
      const text = el("div");
      text.append(el("h3", "", category.label));
      let rule = t("noRequirement");
      if (category.min_ects !== null && category.min_ects !== undefined) rule = `${t("minimum")} ${category.min_ects} ECTS`;
      if (category.max_ects !== null && category.max_ects !== undefined) rule += ` · ${t("maximum")} ${category.max_ects}`;
      text.append(el("div", "progress-card__rule", rule));
      top.append(text, el("div", "progress-card__number", `${amount}`));
      const track = el("div", "progress-track");
      const fill = el("span");
      fill.style.width = `${progress}%`;
      track.append(fill);
      const status = target ? (amount >= target ? t("complete") : `${target - amount} ECTS ${t("remaining")}`) : formatEcts(amount);
      card.append(top, track, el("div", "progress-card__rule", status));
      grid.append(card);
    });

    (state.aggregate_requirements || []).forEach(requirement => {
      const included = new Set(requirement.category_ids);
      const amount = selected.filter(course => included.has(course.category_id)).reduce((sum, course) => sum + (Number(course.ects) || 0), 0);
      const target = requirement.min_ects;
      const progress = target ? Math.min(100, amount / target * 100) : (amount > 0 ? 100 : 0);
      const card = el("article", "progress-card progress-card--aggregate");
      card.style.setProperty("--category-color", "#334155");
      const top = el("div", "progress-card__top");
      const text = el("div");
      text.append(el("h3", "", requirement.label));
      let rule = t("noRequirement");
      if (requirement.min_ects !== null && requirement.min_ects !== undefined) rule = `${t("minimum")} ${requirement.min_ects} ECTS`;
      if (requirement.max_ects !== null && requirement.max_ects !== undefined) rule += ` · ${t("maximum")} ${requirement.max_ects}`;
      text.append(el("div", "progress-card__rule", rule));
      top.append(text, el("div", "progress-card__number", `${amount}`));
      const track = el("div", "progress-track");
      const fill = el("span");
      fill.style.width = `${progress}%`;
      track.append(fill);
      const status = target ? (amount >= target ? t("complete") : `${target - amount} ECTS ${t("remaining")}`) : formatEcts(amount);
      card.append(top, track, el("div", "progress-card__rule", status));
      grid.append(card);
    });

    const unclassified = selected.filter(course => !course.category_id);
    if (unclassified.length) {
      const card = el("article", "progress-card");
      card.style.setProperty("--category-color", colorFor(null));
      const top = el("div", "progress-card__top");
      const label = el("div");
      label.append(el("h3", "", t("unclassified")), el("div", "progress-card__rule", `${unclassified.length} ${t("courses")}`));
      const ects = unclassified.reduce((sum, course) => sum + (Number(course.ects) || 0), 0);
      top.append(label, el("div", "progress-card__number", ects));
      card.append(top);
      grid.append(card);
    }
  }

  function renderCategoryFilter() {
    const select = document.getElementById("category-filter");
    const previous = select.value;
    select.replaceChildren();
    select.append(new Option(t("allCategories"), ""));
    state.categories.forEach(category => select.append(new Option(category.label, category.id)));
    select.append(new Option(t("unclassified"), "__unclassified"));
    if ([...select.options].some(option => option.value === previous)) select.value = previous;
  }

  function tracks() { return Array.isArray(state.tracks) ? state.tracks : []; }
  function trackById(id) { return tracks().find(track => track.id === id); }
  function renderTrackFilters() {
    const region = document.getElementById("track-filters");
    region.replaceChildren();
    if (!tracks().length) return;
    const groups = new Map();
    tracks().forEach(track => {
      const group = track.group || t("tracks");
      if (!groups.has(group)) groups.set(group, []);
      groups.get(group).push(track);
    });
    groups.forEach((items, groupName) => {
      const group = el("div", "track-group");
      group.append(el("div", "track-group__label", groupName));
      items.forEach(track => {
        const button = el("button", `track-chip${activeTrackIds.has(track.id) ? " is-active" : ""}`, track.label);
        button.type = "button";
        button.addEventListener("click", () => {
          if (activeTrackIds.has(track.id)) activeTrackIds.delete(track.id); else activeTrackIds.add(track.id);
          renderTrackFilters(); renderCourses();
        });
        group.append(button);
      });
      region.append(group);
    });
  }

  function filteredCourses() {
    const search = document.getElementById("search-input").value.trim().toLocaleLowerCase();
    const filter = document.getElementById("category-filter").value;
    return state.courses.filter(course => {
      const text = `${course.title} ${course.module_code || ""}`.toLocaleLowerCase();
      const matchesText = !search || text.includes(search);
      const matchesCategory = !filter || (filter === "__unclassified" ? !course.category_id : course.category_id === filter);
      const courseTracks = new Set(course.track_ids || []);
      const matchesTrack = !activeTrackIds.size || [...activeTrackIds].some(id => courseTracks.has(id));
      return matchesText && matchesCategory && matchesTrack;
    });
  }

  function renderCourses() {
    const courses = filteredCourses();
    document.getElementById("course-count").textContent = `${courses.length} ${t("courses")}`;
    const list = document.getElementById("course-list");
    list.replaceChildren();
    if (!courses.length) { list.append(el("div", "empty-state", t("noCourses"))); return; }
    courses.forEach(course => list.append(courseCard(course)));
  }

  function courseCard(course) {
    const selected = course.status === "planned" || course.status === "enrolled";
    const card = el("article", `course-card${selected ? " is-selected" : ""}`);
    card.style.setProperty("--category-color", colorFor(course.category_id));
    const header = el("div", "course-card__header");
    const info = el("div");
    info.append(el("div", "course-card__code", course.module_code || course.id), el("h3", "", course.title));
    const meta = el("div", "course-card__meta");
    meta.append(el("span", "tag", formatEcts(course.ects)));
    const category = categoryById(course.category_id);
    meta.append(el("span", category ? "tag" : "tag tag--unclassified", category?.label || t("unclassified")));
    (course.track_ids || []).map(trackById).filter(Boolean).forEach(track => meta.append(el("span", "tag", track.label)));
    const registration = registrationLabel(course);
    meta.append(el("span", `tag tag--registration is-${course.registration?.status || "unknown"}`, registration));
    info.append(meta);
    const button = el("button", `status-button${selected ? " is-selected" : ""}`);
    button.type = "button";
    if (course.status === "enrolled") {
      button.textContent = t("enrolled");
      button.disabled = true;
    } else {
      button.textContent = selected ? t("remove") : t("add");
      button.addEventListener("click", () => {
        course.status = selected ? "candidate" : "planned";
        if (course.status === "planned" && !course.selected_group_id && course.session_groups?.length) course.selected_group_id = course.session_groups[0].id;
        render();
      });
    }
    header.append(info, button);
    card.append(header);
    if (course.session_groups?.length > 1) {
      const select = el("select", "group-select");
      select.setAttribute("aria-label", `${t("chooseGroup")}: ${course.title}`);
      course.session_groups.forEach(group => select.append(new Option(`${t("chooseGroup")}: ${group.label}`, group.id)));
      select.value = selectedGroup(course)?.id || course.session_groups[0].id;
      select.addEventListener("change", () => { course.selected_group_id = select.value; renderCalendar(); });
      card.append(select);
    }
    return card;
  }

  function registrationLabel(course) {
    const registration = course.registration || {};
    if (registration.label) return registration.label;
    if (registration.status === "open") return t("registrationOpen");
    if (registration.status === "upcoming") return registration.opens_at ? `${t("registrationUpcoming")}: ${registration.opens_at}` : t("registrationUpcoming");
    if (registration.status === "none") return t("registrationNone");
    return t("registrationUnknown");
  }

  function meetingRecords() {
    const records = [];
    selectedCourses().forEach(course => {
      const group = selectedGroup(course);
      (group?.meetings || []).forEach((meeting, index) => records.push({course, group, meeting, key: `${course.id}:${group.id}:${index}`}));
    });
    return records;
  }

  function conflictKeys(records) {
    const keys = new Set();
    for (let i = 0; i < records.length; i += 1) {
      for (let j = i + 1; j < records.length; j += 1) {
        const a = records[i], b = records[j];
        if (a.course.id === b.course.id || a.meeting.day !== b.meeting.day) continue;
        if (minutes(a.meeting.start) < minutes(b.meeting.end) && minutes(b.meeting.start) < minutes(a.meeting.end)) {
          keys.add(a.key); keys.add(b.key);
        }
      }
    }
    return keys;
  }

  function renderCalendar() {
    const records = meetingRecords();
    const conflicts = conflictKeys(records);
    const conflictCount = [...conflicts].length;
    const chip = document.getElementById("conflict-chip");
    chip.textContent = conflictCount ? `${conflictCount} ${t("conflicts")}` : t("noConflicts");
    chip.classList.toggle("has-conflict", Boolean(conflictCount));

    const dayNames = language === "zh" ? ["周一", "周二", "周三", "周四", "周五", "周六", "周日"] : ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const calendar = document.getElementById("calendar");
    calendar.replaceChildren();
    for (let day = 1; day <= 7; day += 1) {
      const column = el("div", "day-column");
      column.append(el("div", "day-title", dayNames[day - 1]));
      records.filter(record => record.meeting.day === day).forEach(record => {
        const event = el("div", `event${conflicts.has(record.key) ? " is-conflict" : ""}`);
        event.style.setProperty("--category-color", colorFor(record.course.category_id));
        event.style.top = `${40 + Math.max(0, minutes(record.meeting.start) - DAY_START_MINUTES) * PIXELS_PER_MINUTE}px`;
        event.style.minHeight = `${Math.max(92, (minutes(record.meeting.end) - minutes(record.meeting.start)) * PIXELS_PER_MINUTE)}px`;
        event.title = `${record.course.title}\n${record.meeting.start}–${record.meeting.end}\n${record.meeting.location || ""}`;
        event.append(el("strong", "", record.course.title), el("span", "", `${record.meeting.start}–${record.meeting.end}`));
        if (record.meeting.location) event.append(el("span", "", ` · ${record.meeting.location}`));
        event.append(el("small", "event__registration", registrationLabel(record.course)));
        column.append(event);
      });
      calendar.append(column);
    }
    const scheduledSummary = document.getElementById("scheduled-summary");
    scheduledSummary.replaceChildren();
    const scheduledCourses = selectedCourses().filter(course => (selectedGroup(course)?.meetings || []).length);
    if (scheduledCourses.length) {
      scheduledSummary.append(el("h3", "", t("scheduledCourses")));
      const summaryList = el("div", "scheduled-summary-list");
      scheduledCourses.forEach(course => {
        const group = selectedGroup(course);
        const meetings = group.meetings.map(meeting => {
          const day = language === "zh" ? `周${"一二三四五六日"[meeting.day - 1]}` : ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][meeting.day - 1];
          return `${day} ${meeting.start}–${meeting.end}`;
        }).join("; ");
        const item = el("div", "scheduled-summary-item");
        item.style.setProperty("--category-color", colorFor(course.category_id));
        item.append(el("strong", "", course.title), el("span", "", meetings), el("small", "", registrationLabel(course)));
        summaryList.append(item);
      });
      scheduledSummary.append(summaryList);
    }
    const unscheduled = document.getElementById("unscheduled");
    unscheduled.replaceChildren();
    const items = selectedCourses().filter(course => !(selectedGroup(course)?.meetings || []).length);
    if (items.length) {
      unscheduled.append(el("h3", "", t("noTime")));
      const list = el("div", "unscheduled-list");
      items.forEach(course => {
        const item = el("span", "unscheduled-item");
        const timeLabel = course.schedule_status === "unpublished" ? t("noTimePublished") : course.schedule_status === "unverified" ? t("detailPending") : t("timeTba");
        item.append(el("strong", "", course.title), el("span", "", timeLabel), el("small", "", registrationLabel(course)));
        item.style.setProperty("--category-color", colorFor(course.category_id));
        list.append(item);
      });
      unscheduled.append(list);
    }
  }

  function renderEvidence() {
    const sources = [];
    const seen = new Set();
    [state.program.source, ...state.categories.map(item => item.source), ...(state.aggregate_requirements || []).map(item => item.source), ...state.courses.flatMap(item => [item.source, ...(item.evidence || [])])].forEach(source => {
      if (!source) return;
      const key = `${source.kind}|${source.label}|${source.url || ""}|${source.observed_at}`;
      if (!seen.has(key)) { seen.add(key); sources.push(source); }
    });
    const list = document.getElementById("evidence-list");
    list.replaceChildren();
    sources.forEach(source => {
      const row = el("div", "evidence-item");
      row.append(el("div", "evidence-kind", source.kind.replaceAll("_", " ")));
      if (source.url) {
        const link = el("a", "", source.label);
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noreferrer noopener";
        row.append(link);
      } else row.append(el("div", "", source.label));
      row.append(el("div", "evidence-time", formatObserved(source.observed_at)));
      list.append(row);
    });
  }

  function containsSensitiveKey(value) {
    if (Array.isArray(value)) return value.some(containsSensitiveKey);
    if (value && typeof value === "object") return Object.entries(value).some(([key, child]) => SENSITIVE_KEY.test(key) || containsSensitiveKey(child));
    return false;
  }

  function minimallyValidateImport(value) {
    if (!value || typeof value !== "object" || value.schema_version !== "1.0") throw new Error("schema_version must be 1.0");
    if (containsSensitiveKey(value)) throw new Error("file contains prohibited personal-data fields");
    const target = value.planning_term?.target?.code;
    if (!target || !Array.isArray(value.courses) || !Array.isArray(value.categories)) throw new Error("missing required planner fields");
    if (value.courses.some(course => course.term !== target)) throw new Error("course term does not match target term");
  }

  document.getElementById("language-button").addEventListener("click", () => { language = language === "en" ? "zh" : "en"; render(); });
  document.getElementById("search-input").addEventListener("input", renderCourses);
  document.getElementById("category-filter").addEventListener("change", renderCourses);
  document.getElementById("print-button").addEventListener("click", () => window.print());
  document.getElementById("import-button").addEventListener("click", () => document.getElementById("import-file").click());
  document.getElementById("import-file").addEventListener("change", async event => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const value = JSON.parse(await file.text());
      minimallyValidateImport(value);
      state = value;
      activeTrackIds = new Set();
      transientNotice = {message: t("imported"), error: false};
      render();
    } catch (error) {
      transientNotice = {message: `${t("importError")}: ${error.message}`, error: true};
      renderNotices();
    } finally { event.target.value = ""; }
  });
  document.getElementById("export-button").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `tum-elective-plan-${state.planning_term.target.code}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  document.getElementById("select-visible-button").addEventListener("click", () => {
    filteredCourses().forEach(course => { if (course.status !== "enrolled") course.status = "planned"; }); render();
  });
  document.getElementById("clear-visible-button").addEventListener("click", () => {
    filteredCourses().forEach(course => { if (course.status !== "enrolled") course.status = "candidate"; }); render();
  });
  function applyViewScale() {
    const font = document.getElementById("font-scale").value;
    const calendar = document.getElementById("calendar-scale").value;
    document.documentElement.style.fontSize = `${font}%`;
    document.documentElement.style.setProperty("--calendar-width", `${calendar}%`);
    document.getElementById("font-scale-output").textContent = `${font}%`;
    document.getElementById("calendar-scale-output").textContent = `${calendar}%`;
  }
  document.getElementById("font-scale").addEventListener("input", applyViewScale);
  document.getElementById("calendar-scale").addEventListener("input", applyViewScale);
  applyViewScale();

  render();
})();
