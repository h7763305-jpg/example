const companies = [
  {
    name: "株式会社アルファSaaS",
    industry: "SaaS",
    roles: ["バックエンドエンジニア", "テックリード候補"],
    requiredSkills: ["Python", "FastAPI"],
    preferredSkills: ["AWS", "Terraform"],
    location: "東京",
    remote: "週3日リモート可",
    salary: [650, 900],
    culture: ["自社プロダクト", "技術的裁量", "少人数チーム"],
    workload: "平均残業20時間未満",
    hiringNote: "バックエンドの中核メンバーを採用中",
  },
  {
    name: "株式会社ベータHR",
    industry: "HRTech",
    roles: ["バックエンドエンジニア"],
    requiredSkills: ["Python"],
    preferredSkills: ["FastAPI", "AWS"],
    location: "東京",
    remote: "フルリモート相談可",
    salary: [700, 1000],
    culture: ["自社プロダクト", "ユーザー志向", "技術改善に積極的"],
    workload: "繁忙期は残業が増える可能性あり",
    hiringNote: "HR領域の新規プロダクト開発",
  },
  {
    name: "株式会社ガンマSI",
    industry: "受託開発",
    roles: ["バックエンドエンジニア"],
    requiredSkills: ["Python"],
    preferredSkills: ["Django"],
    location: "東京",
    remote: "原則出社",
    salary: [550, 750],
    culture: ["顧客常駐", "短納期案件が多い"],
    workload: "案件により残業が多い",
    hiringNote: "複数の受託案件で即戦力を募集",
  },
  {
    name: "株式会社デルタAI",
    industry: "AI",
    roles: ["機械学習エンジニア"],
    requiredSkills: ["Python", "機械学習"],
    preferredSkills: ["AWS", "MLOps"],
    location: "大阪",
    remote: "週1日リモート可",
    salary: [700, 950],
    culture: ["研究開発", "技術的裁量"],
    workload: "開発フェーズにより変動",
    hiringNote: "機械学習モデル開発経験を重視",
  },
  {
    name: "株式会社イプシロンUI",
    industry: "SaaS",
    roles: ["フロントエンドエンジニア"],
    requiredSkills: ["React", "TypeScript"],
    preferredSkills: ["AWS"],
    location: "東京",
    remote: "週3日リモート可",
    salary: [600, 850],
    culture: ["自社プロダクト", "ユーザー志向", "技術的裁量"],
    workload: "平均残業15時間未満",
    hiringNote: "管理画面とデザインシステムの改善を担当",
  },
  {
    name: "株式会社ゼータFinTech",
    industry: "FinTech",
    roles: ["フルスタックエンジニア", "バックエンドエンジニア"],
    requiredSkills: ["TypeScript", "Node.js"],
    preferredSkills: ["React", "AWS", "Python"],
    location: "福岡",
    remote: "フルリモート可",
    salary: [650, 950],
    culture: ["プロダクト志向", "裁量大きめ", "セキュリティ重視"],
    workload: "リリース前は調整が必要",
    hiringNote: "決済基盤と管理画面の開発を担当",
  },
];

const samples = {
  backend:
    "現職はバックエンドエンジニアで、PythonとFastAPIを使ったAPI開発を担当しています。AWSも少し経験があります。次は自社プロダクトで技術的裁量がある環境を希望しています。勤務地は東京、週2日以上はリモート希望です。年収は700万円以上を目指しています。短納期の受託案件や残業が多い環境は避けたいです。",
  frontend:
    "ReactとTypeScriptで管理画面やデザインシステムを作ってきました。ユーザー志向のSaaS企業で、フロントエンドエンジニアとしてプロダクト改善に関わりたいです。東京勤務、週3日程度のリモートを希望します。希望年収は650万円前後です。技術的裁量がある会社だと合いそうです。",
  ai:
    "Pythonでデータ分析と機械学習モデルの開発を経験しています。MLOpsやAWSにも興味があります。AI領域の研究開発に近い環境で働きたいです。大阪勤務も検討できます。リモートは週1日でも問題ありません。希望年収は750万円以上です。",
};

const selectors = {
  input: document.querySelector("#interviewInput"),
  results: document.querySelector("#companyResults"),
  signals: document.querySelector("#profileSignals"),
  signalCount: document.querySelector("#signalCount"),
  resultSummary: document.querySelector("#resultSummary"),
  statusPanel: document.querySelector(".status-panel"),
  statusText: document.querySelector("#statusText"),
  clearButton: document.querySelector("#clearButton"),
  reloadSampleButton: document.querySelector("#reloadSampleButton"),
  sampleButtons: document.querySelectorAll(".sample-button"),
  filterButtons: document.querySelectorAll(".filter-button"),
};

let activeSample = "backend";
let activeFilter = "all";
let latestMatches = [];

// 入力文の表記ゆれを吸収するため、抽出したい条件ごとに拾う語句をまとめる。
const dictionaries = {
  skills: [
    "Python",
    "FastAPI",
    "AWS",
    "Terraform",
    "Django",
    "React",
    "TypeScript",
    "Node.js",
    "機械学習",
    "MLOps",
  ],
  roles: [
    "バックエンドエンジニア",
    "フロントエンドエンジニア",
    "機械学習エンジニア",
    "フルスタックエンジニア",
    "テックリード",
  ],
  industries: ["SaaS", "HRTech", "AI", "FinTech", "受託開発"],
  locations: ["東京", "大阪", "福岡"],
  values: ["自社プロダクト", "技術的裁量", "ユーザー志向", "研究開発", "少人数チーム"],
  avoid: ["残業が多い", "短納期", "受託", "常駐", "原則出社"],
};

function normalizeText(text) {
  return text.toLowerCase().replace(/\s+/g, "");
}

function includesTerm(text, term) {
  return normalizeText(text).includes(normalizeText(term));
}

function unique(values) {
  return [...new Set(values)];
}

// 面談入力から、企業照合に使う候補者条件だけを取り出す。
function extractProfile(text) {
  const salaryMatch = text.match(/(\d{3,4})\s*万円以上|年収は?(\d{3,4})\s*万円|希望年収は?(\d{3,4})\s*万円/);
  const remoteFlexible = /週1日でも問題|リモートは少なくても|出社も可能/.test(text);
  const remoteRequired = /フルリモート|週[2-5]日.*リモート|リモート希望|リモートを希望/.test(text);

  return {
    skills: unique(dictionaries.skills.filter((term) => includesTerm(text, term))),
    roles: unique(dictionaries.roles.filter((term) => includesTerm(text, term))),
    industries: unique(dictionaries.industries.filter((term) => includesTerm(text, term))),
    locations: unique(dictionaries.locations.filter((term) => includesTerm(text, term))),
    values: unique(dictionaries.values.filter((term) => includesTerm(text, term))),
    avoid: unique(dictionaries.avoid.filter((term) => includesTerm(text, term))),
    salary: salaryMatch ? Number(salaryMatch[1] || salaryMatch[2] || salaryMatch[3]) : null,
    remotePreference: remoteFlexible ? "柔軟" : remoteRequired ? "リモート重視" : "",
  };
}

function hasOverlap(left, right) {
  return left.some((item) => right.some((target) => includesTerm(target, item) || includesTerm(item, target)));
}

// 内部では重みを使って並び順を決めるが、画面には点数として出さない。
function matchCompany(company, profile) {
  let weight = 0;
  const reasons = [];
  const concerns = [];
  const questions = [];
  const allSkills = [...company.requiredSkills, ...company.preferredSkills];

  if (profile.roles.length && hasOverlap(profile.roles, company.roles)) {
    weight += 4;
    reasons.push(`希望職種と募集職種が近い: ${company.roles.join(" / ")}`);
  }

  if (profile.skills.length && hasOverlap(profile.skills, allSkills)) {
    weight += 4;
    const matchedSkills = profile.skills.filter((skill) => hasOverlap([skill], allSkills));
    reasons.push(`経験スキルを活かしやすい: ${matchedSkills.join(" / ")}`);
  }

  if (profile.industries.length && profile.industries.includes(company.industry)) {
    weight += 2;
    reasons.push(`希望業界と一致: ${company.industry}`);
  }

  if (profile.locations.length && profile.locations.includes(company.location)) {
    weight += 2;
    reasons.push(`希望勤務地と一致: ${company.location}`);
  } else if (profile.locations.length && company.remote.includes("フルリモート")) {
    weight += 1;
    reasons.push("勤務地の差をリモート条件で調整しやすい");
  }

  if (profile.remotePreference === "リモート重視" && /フルリモート|週[2-5]日リモート/.test(company.remote)) {
    weight += 2;
    reasons.push(`リモート希望と近い: ${company.remote}`);
  } else if (profile.remotePreference === "リモート重視" && company.remote.includes("原則出社")) {
    weight -= 3;
    concerns.push("リモート希望に対して出社前提の可能性があります。");
    questions.push("出社頻度の許容範囲を確認してください。");
  } else if (profile.remotePreference === "柔軟" && !company.remote.includes("原則出社")) {
    weight += 1;
    reasons.push(`リモート条件が大きな障壁になりにくい: ${company.remote}`);
  }

  if (profile.salary) {
    if (profile.salary <= company.salary[1] && profile.salary >= company.salary[0] - 50) {
      weight += 2;
      reasons.push(`希望年収とレンジが近い: ${company.salary[0]}万円-${company.salary[1]}万円`);
    } else if (profile.salary > company.salary[1]) {
      weight -= 2;
      concerns.push("希望年収が提示レンジを上回る可能性があります。");
      questions.push("年収条件の優先度と下限を確認してください。");
    }
  }

  const cultureHits = profile.values.filter((value) => company.culture.some((item) => includesTerm(item, value)));
  if (cultureHits.length) {
    weight += 2;
    reasons.push(`重視する価値観と近い: ${cultureHits.join(" / ")}`);
  }

  if (profile.avoid.some((term) => includesTerm(company.workload, term) || company.culture.some((item) => includesTerm(item, term)))) {
    weight -= 3;
    concerns.push("避けたい条件に近い要素があります。");
    questions.push("残業・案件特性・働き方の許容範囲を確認してください。");
  }

  if (!reasons.length) {
    concerns.push("入力内容と企業条件の明確な一致がまだ少ないです。");
    questions.push("希望職種、スキル、勤務地、働き方を追加で確認してください。");
  }

  return {
    company,
    weight,
    label: getSelectionLabel(weight, concerns.length),
    reasons: reasons.slice(0, 4),
    concerns: concerns.length ? unique(concerns) : ["現時点で大きな懸念点は少ないです。"],
    questions: unique(questions).slice(0, 3),
  };
}

function getSelectionLabel(weight, concernCount) {
  if (weight >= 9 && concernCount === 0) return "マッチ度が高い";
  if (weight >= 6) return "マッチしている";
  if (weight >= 3) return "条件確認が必要";
  return "現時点ではマッチが弱い";
}

function buildSignals(profile) {
  const signals = [
    ...profile.roles.map((value) => ({ kind: "職種", value })),
    ...profile.skills.map((value) => ({ kind: "スキル", value })),
    ...profile.industries.map((value) => ({ kind: "業界", value })),
    ...profile.locations.map((value) => ({ kind: "勤務地", value })),
    ...profile.values.map((value) => ({ kind: "価値観", value })),
    ...profile.avoid.map((value) => ({ kind: "懸念", value })),
  ];

  if (profile.remotePreference) {
    signals.push({ kind: "働き方", value: profile.remotePreference });
  }

  if (profile.salary) {
    signals.push({ kind: "年収", value: `${profile.salary}万円以上` });
  }

  return signals;
}

function renderSignals(signals) {
  selectors.signals.replaceChildren();
  selectors.signalCount.textContent = `${signals.length}件`;

  if (!signals.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "抽出条件なし";
    selectors.signals.append(empty);
    return;
  }

  signals.forEach((signal) => {
    const chip = document.createElement("span");
    chip.className = "signal-chip";
    chip.dataset.kind = signal.kind;
    chip.textContent = `${signal.kind}: ${signal.value}`;
    selectors.signals.append(chip);
  });
}

function renderList(title, items, className = "") {
  const group = document.createElement("div");
  group.className = "detail-group";

  const heading = document.createElement("p");
  heading.className = "detail-title";
  heading.textContent = title;

  const list = document.createElement("ul");
  list.className = `detail-list ${className}`.trim();

  items.forEach((item) => {
    const row = document.createElement("li");
    row.textContent = item;
    list.append(row);
  });

  group.append(heading, list);
  return group;
}

function renderCompanyCard(match) {
  const { company } = match;
  const card = document.createElement("article");
  card.className = "company-card";
  card.dataset.label = match.label;

  const topline = document.createElement("div");
  topline.className = "company-topline";

  const titleBlock = document.createElement("div");
  const name = document.createElement("h3");
  name.className = "company-name";
  name.textContent = company.name;
  const note = document.createElement("p");
  note.className = "muted";
  note.textContent = company.hiringNote;
  titleBlock.append(name, note);

  const label = document.createElement("span");
  label.className = "label-pill";
  label.textContent = match.label;
  topline.append(titleBlock, label);

  const meta = document.createElement("div");
  meta.className = "company-meta";
  [company.industry, company.location, company.remote, `${company.salary[0]}万円-${company.salary[1]}万円`].forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "meta-chip";
    chip.textContent = item;
    meta.append(chip);
  });

  card.append(
    topline,
    meta,
    renderList("選出理由", match.reasons.length ? match.reasons : ["追加条件の入力後に照合します。"]),
    renderList("懸念点", match.concerns, "concerns"),
    renderList("追加確認すべき質問", match.questions.length ? match.questions : ["本人の優先順位を確認してください。"]),
  );

  return card;
}

function applyFilter(matches) {
  if (activeFilter === "strong") {
    return matches.filter((match) => match.label === "マッチ度が高い" || match.label === "マッチしている");
  }

  if (activeFilter === "check") {
    return matches.filter((match) => match.label === "条件確認が必要" || match.label === "現時点ではマッチが弱い");
  }

  return matches;
}

function renderResults(matches) {
  selectors.results.replaceChildren();
  const visibleMatches = applyFilter(matches);

  if (!visibleMatches.length) {
    const empty = document.createElement("div");
    empty.className = "no-results";
    empty.textContent = "表示できる選出企業がありません。";
    selectors.results.append(empty);
    return;
  }

  visibleMatches.forEach((match, index) => {
    const card = renderCompanyCard(match);
    card.style.animationDelay = `${index * 45}ms`;
    selectors.results.append(card);
  });
}

function updateSearch() {
  const text = selectors.input.value.trim();
  const profile = extractProfile(text);
  const signals = buildSignals(profile);

  latestMatches = companies
    .map((company) => matchCompany(company, profile))
    .sort((a, b) => b.weight - a.weight);

  renderSignals(signals);
  renderResults(latestMatches);

  selectors.statusPanel.classList.toggle("is-active", Boolean(text));
  selectors.statusText.textContent = text ? "照合中" : "入力待ち";
  selectors.resultSummary.textContent = text
    ? `${latestMatches.length}社を照合しました。`
    : "入力内容から企業を照合します。";
}

function setSample(sampleName) {
  activeSample = sampleName;
  selectors.input.value = samples[sampleName];
  selectors.sampleButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.sample === sampleName);
  });
  updateSearch();
}

selectors.sampleButtons.forEach((button) => {
  button.addEventListener("click", () => setSample(button.dataset.sample));
});

selectors.filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;
    selectors.filterButtons.forEach((item) => item.classList.toggle("active", item === button));
    renderResults(latestMatches);
  });
});

selectors.input.addEventListener("input", updateSearch);
selectors.clearButton.addEventListener("click", () => {
  selectors.input.value = "";
  updateSearch();
  selectors.input.focus();
});
selectors.reloadSampleButton.addEventListener("click", () => setSample(activeSample));

setSample(activeSample);
