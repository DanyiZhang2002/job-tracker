// ====== STATE ======
let allJobs = [];
let appliedJobs = JSON.parse(localStorage.getItem('applied_jobs') || '[]');
let userProfile = JSON.parse(localStorage.getItem('user_profile') || '{}');
let userTags = JSON.parse(localStorage.getItem('user_tags') || '[]');
let currentJob = null;
let currentSTab = 'resume';
let currentMainTab = 'private'; // 'private' | 'state'

// ====== MAIN TAB SWITCH ======
async function switchMainTab(tab) {
  currentMainTab = tab;
  document.querySelectorAll('.main-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(`mtab-${tab}`).classList.add('active');
  await loadJobs();
  showPage('jobs');
}

// ====== INIT ======
async function init() {
  await loadJobs();
  updateAppliedBadge();
}

async function loadJobs() {
  try {
    const file = currentMainTab === 'state' ? 'data/state_jobs.json' : 'data/jobs.json';
    const r = await fetch(`${file}?v=${Date.now()}`);
    const data = await r.json();
    allJobs = data.jobs;
    document.getElementById('total-count').textContent = `${allJobs.length} 个岗位`;
    document.getElementById('update-time').textContent = `更新于 ${data.lastUpdated}`;
    renderJobs(allJobs);
  } catch (e) {
    document.getElementById('cards-container').innerHTML = '<div class="no-results"><div>⚠️</div><p>数据加载失败，请刷新重试</p></div>';
  }
}

// ====== RENDER JOBS ======
// 公司类型分区配置
const STATE_SECTIONS = [
  { key: '国有銀行', label: '🏦 国有大行', badge: 'state-bank' },
  { key: '国有证券', label: '📈 国有证券', badge: 'state-sec' },
  { key: '国有保险', label: '🛡️ 国有保险', badge: 'state-ins' },
  { key: '央企（通信/科技）', label: '📡 通信技术央企', badge: 'state-tech' },
  { key: '央企（能源）', label: '⚡ 能源央企', badge: 'state-energy' },
  { key: '央企（航空/制造）', label: '✈️ 航空制造央企', badge: 'state-mfg' },
  { key: '央企（消费/地产）', label: '🌿 消费地产央企', badge: 'state-cons' },
  { key: '央企（交通/基建）', label: '🚄 交通基建央企', badge: 'state-infra' },
];

const COMPANY_SECTIONS = [
  { key: '互联网大厂', label: '📱 互联网大厂', badge: 'internet' },
  { key: '外资投行&咨询', label: '🏛️ 外资投行 & 咨询', badge: 'foreign' },
  { key: '国内金融&财务', label: '💰 国内金融 & 财务', badge: 'finance' },
  { key: '其他', label: '📋 其他', badge: 'other' },
];

// 外资投行&咨询内部子分类
const FOREIGN_SUB_SECTIONS = [
  { key: '投行', label: '🏛️ 投行（Investment Banking）', cats: ['投行'] },
  { key: '和咨询', label: '🎯 战略和咨询（MBB & Big4）', cats: ['咨询'] },
  { key: '金融其他', label: '💹 金融 & 其他', cats: ['金融', '财务'] },
  { key: '数据技术', label: '🤖 数据 & 技术', cats: ['数据科学', 'AI', '后端开发'] },
];

// 互联网大厂内部子分类
const INTERNET_SUB_SECTIONS = [
  { key: '技术开发', label: '🖥️ 技术开发', cats: ['后端开发', '前端开发'] },
  { key: 'AI与数据', label: '🤖 AI & 数据', cats: ['AI', '数据科学'] },
  { key: '产品', label: '📱 产品', cats: ['数据产品'] },
  { key: '运营与商务', label: '📣 运营 & 商务', cats: ['策略运营'] },
];

function renderJobs(jobs) {
  const container = document.getElementById('cards-container');
  if (!jobs.length) {
    container.innerHTML = '<div class="no-results"><div>🔍</div><p>没有找到匹配的岗位</p></div>';
    return;
  }

  let html = '';
  const sections = currentMainTab === 'state' ? STATE_SECTIONS : COMPANY_SECTIONS;
  sections.forEach(section => {
    const group = jobs.filter(j => (j.companyType || '其他') === section.key);
    if (!group.length) return;

    html += `<div class="section-header">
      <span class="section-badge ${section.badge}">${section.label}</span>
      <span class="section-count">${group.length} 个岗位</span>
    </div>`;

    if (section.key === '互联网大厂') {
      // 互联网大厂内部按子分类渲染
      INTERNET_SUB_SECTIONS.forEach(sub => {
        const subGroup = group.filter(j =>
          j.category && j.category.some(c => sub.cats.includes(c))
        );
        if (!subGroup.length) return;
        html += `
          <div class="sub-section-header">
            <span class="sub-section-label">${sub.label}</span>
            <span class="sub-section-count">${subGroup.length} 个岗位</span>
          </div>
          <div class="cards-grid">${subGroup.map(makeCard).join('')}</div>
        `;
      });
      // 未归类的放到「其他方向」
      const allCats = INTERNET_SUB_SECTIONS.flatMap(s => s.cats);
      const rest = group.filter(j =>
        !j.category || !j.category.some(c => allCats.includes(c))
      );
      if (rest.length) {
        html += `
          <div class="sub-section-header">
            <span class="sub-section-label">📋 其他方向</span>
            <span class="sub-section-count">${rest.length} 个岗位</span>
          </div>
          <div class="cards-grid">${rest.map(makeCard).join('')}</div>
        `;
      }
    } else if (section.key === '外资投行&咨询') {
      FOREIGN_SUB_SECTIONS.forEach(sub => {
        const subGroup = group.filter(j =>
          j.category && j.category.some(c => sub.cats.includes(c))
        );
        if (!subGroup.length) return;
        html += `
          <div class="sub-section-header">
            <span class="sub-section-label">${sub.label}</span>
            <span class="sub-section-count">${subGroup.length} 个岗位</span>
          </div>
          <div class="cards-grid">${subGroup.map(makeCard).join('')}</div>
        `;
      });
      const allFCats = FOREIGN_SUB_SECTIONS.flatMap(s => s.cats);
      const restF = group.filter(j => !j.category || !j.category.some(c => allFCats.includes(c)));
      if (restF.length) {
        html += `<div class="sub-section-header"><span class="sub-section-label">📋 其他</span><span class="sub-section-count">${restF.length} 个岗位</span></div>
        <div class="cards-grid">${restF.map(makeCard).join('')}</div>`;
      }
    } else {
      html += `<div class="cards-grid">${group.map(makeCard).join('')}</div>`;
    }
  });

  container.innerHTML = html;
}

function makeCard(job) {
  const isApplied = appliedJobs.some(a => a.id === job.id);
  const deadlineClass = getDeadlineClass(job.deadline);
  const daysLeft = getDaysLeft(job.deadline);

  return `<div class="job-card ${job.isNew ? 'is-new' : ''} ${isApplied ? 'is-applied' : ''}" id="card-${job.id}">
    <div class="card-top">
      <div class="card-company-row">
        <span class="company-logo">${job.logo}</span>
        <span class="company-name">${job.company}</span>
        <span class="tier-badge ${job.tier}">${job.tier}</span>
        ${job.isNew ? '<span class="new-badge">NEW</span>' : ''}
      </div>
      <div class="card-position">${job.position}</div>
      <div class="card-meta">
        <span>📍 ${job.location}</span>
        <span>👥 ${job.headcount}</span>
        <span>📅 ${job.season}</span>
      </div>
      <div class="card-tags">${job.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>
      <div class="card-deadline ${deadlineClass}">
        ⏰ 截止 ${job.deadline}${daysLeft !== null ? `（还有 ${daysLeft} 天）` : ''}
      </div>
    </div>
    <div class="card-actions">
      <button class="btn-view" onclick="openModal(${job.id})">查看详情 →</button>
      <button class="btn-apply ${isApplied ? 'applied' : ''}" id="apply-btn-${job.id}" onclick="${isApplied ? '' : `markApplied(${job.id})`}">
        ${isApplied ? '✅ 已投递' : '＋ 投递此岗位'}
      </button>
    </div>
  </div>`;
}

function getDeadlineClass(deadline) {
  const days = getDaysLeft(deadline);
  if (days === null) return 'normal';
  if (days <= 7) return 'urgent';
  if (days <= 21) return 'soon';
  return 'normal';
}

function getDaysLeft(deadline) {
  if (!deadline) return null;
  const diff = new Date(deadline) - new Date();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

// ====== FILTERS ======
function applyFilters() {
  const search = document.getElementById('search-input').value.toLowerCase();
  const category = document.getElementById('category-filter').value;
  const company = document.getElementById('company-filter').value;
  const tier = document.getElementById('tier-filter').value;
  const newOnly = document.getElementById('new-only').checked;

  const filtered = allJobs.filter(job => {
    const matchSearch = !search ||
      job.company.toLowerCase().includes(search) ||
      job.position.toLowerCase().includes(search) ||
      job.tags.some(t => t.toLowerCase().includes(search));
    const matchCategory = !category || job.category.includes(category);
    const matchCompany = !company || job.company === company;
    const matchTier = !tier || job.tier === tier;
    const matchNew = !newOnly || job.isNew;
    return matchSearch && matchCategory && matchCompany && matchTier && matchNew;
  });

  renderJobs(filtered);
}

// ====== MODAL ======
function openModal(id) {
  currentJob = allJobs.find(j => j.id === id);
  if (!currentJob) return;
  const isApplied = appliedJobs.some(a => a.id === id);

  document.getElementById('modal-content').innerHTML = `
    <h2 style="font-size:1.3rem;font-weight:700;margin-bottom:0.5rem">${currentJob.position}</h2>
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1.2rem">
      <span style="font-size:1.5rem">${currentJob.logo}</span>
      <span style="font-size:1rem;font-weight:600">${currentJob.company}</span>
      <span class="tier-badge ${currentJob.tier}">${currentJob.tier}</span>
      ${currentJob.isNew ? '<span class="new-badge">NEW</span>' : ''}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;margin-bottom:1.2rem;font-size:0.88rem">
      <div><span style="color:#999">📍 地点</span><br/><strong>${currentJob.location}</strong></div>
      <div><span style="color:#999">📅 季节</span><br/><strong>${currentJob.season}</strong></div>
      <div><span style="color:#999">👥 招聘人数</span><br/><strong>${currentJob.headcount}</strong></div>
      <div><span style="color:#999">⏰ 截止日期</span><br/><strong style="color:#e94560">${currentJob.deadline}</strong></div>
    </div>
    <div style="margin-bottom:1.2rem">
      <div style="font-weight:600;margin-bottom:0.4rem;font-size:0.9rem">岗位描述</div>
      <p style="font-size:0.88rem;color:#555;line-height:1.6">${currentJob.description}</p>
    </div>
    <div style="margin-bottom:1.5rem">
      <div style="font-weight:600;margin-bottom:0.4rem;font-size:0.9rem">要求</div>
      <ul style="font-size:0.88rem;color:#555;line-height:1.8;padding-left:1.2rem">
        ${currentJob.requirements.map(r => `<li>${r}</li>`).join('')}
      </ul>
    </div>
    <div style="display:flex;flex-direction:column;gap:0.6rem">
      <a href="${currentJob.applyUrl}" target="_blank" style="display:block;width:100%;padding:0.7rem;background:#1a1a2e;color:white;text-align:center;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.9rem">前往官网投递 →</a>
      <button onclick="openMaterials(${currentJob.id})" style="padding:0.7rem;background:#fff1f0;color:#e94560;border:2px solid #e94560;border-radius:8px;font-weight:600;font-size:0.9rem;cursor:pointer;width:100%">✨ 一键生成申请材料</button>
      <button onclick="markApplied(${currentJob.id});closeModal()" class="${isApplied ? 'btn-apply applied' : 'btn-apply'}" style="padding:0.7rem;border-radius:8px;font-weight:600;font-size:0.9rem;cursor:pointer;width:100%;${isApplied ? 'background:#f6ffed;color:#52c41a;border:2px solid #52c41a' : 'background:white;color:#e94560;border:2px solid #e94560'}">
        ${isApplied ? '✅ 已标记为已投递' : '＋ 标记为已投递'}
      </button>
    </div>
  `;

  document.getElementById('modal-overlay').classList.add('active');
  document.getElementById('job-modal').classList.add('active');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
  document.getElementById('job-modal').classList.remove('active');
}

// ====== MATERIALS ======
function openMaterials(id) {
  currentJob = allJobs.find(j => j.id === id);
  generateMaterials();
  document.getElementById('material-sidebar').classList.add('open');
}

function closeSidebar() {
  document.getElementById('material-sidebar').classList.remove('open');
}

function switchSTab(tab) {
  currentSTab = tab;
  document.querySelectorAll('.stab').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  generateMaterials();
}

function generateMaterials() {
  if (!currentJob) return;
  const profile = userProfile;
  const name = profile.name || '你的姓名';
  const edu1 = profile.edu1 || '最高学历';
  const skills = profile.skills || 'Python, SQL, 数据分析';
  const exp = profile.exp || '相关实习/研究经历';

  let content = '';

  if (currentSTab === 'resume') {
    content = `📄 简历亮点 — 针对「${currentJob.company} · ${currentJob.position}」

━━━━━━━━━━━━━━━━━━━━
${name}
${edu1}

【核心技能匹配】
${currentJob.tags.map(t => `✓ ${t}`).join('\n')}

【建议重点突出的经历】
${currentJob.requirements.map(r => `→ 针对「${r}」：展示你具体的项目经历和量化成果`).join('\n')}

【技能关键词（确保出现在简历中）】
${skills}

【岗位要求对照】
${currentJob.requirements.map((r, i) => `${i+1}. ${r}`).join('\n')}

【建议】
1. 简历头部用数字量化成果（如：提升XX%、处理XX万条数据）
2. 技能栏与岗位标签高度匹配：${currentJob.tags.join('、')}
3. 项目经历与「${currentJob.position}」的核心职责对应
`;
  } else if (currentSTab === 'coverletter') {
    content = `✍️ 求职信 — 「${currentJob.company} · ${currentJob.position}」

━━━━━━━━━━━━━━━━━━━━
尊敬的${currentJob.company}招聘团队，

我是${name}，${edu1}，现申请贵司${currentJob.season}「${currentJob.position}」岗位。

【为什么选择${currentJob.company}】
${currentJob.company}在${currentJob.category.join('、')}领域的布局和技术积累令我深度认同，尤其是在${currentJob.tags[0]}和${currentJob.tags[1] || currentJob.tags[0]}方向的前沿探索，与我的研究方向高度契合。

【我能带来什么】
在${edu1}的学习过程中，我系统掌握了${skills.split(',').slice(0,3).join('、')}等核心技能。${exp}

【具体能力匹配】
${currentJob.requirements.slice(0,3).map(r => `· ${r}：[请补充你的具体经历和成果]`).join('\n')}

期待有机会加入${currentJob.company}，为${currentJob.position}方向贡献力量。

此致
${name}
`;
  } else {
    content = `🤖 AI提示词 — 复制到 Kimi/ChatGPT/Claude 等工具使用

━━━━━━━━━━━━━━━━━━━━
请你帮我优化一份针对以下岗位的求职材料：

【目标岗位】
公司：${currentJob.company}
职位：${currentJob.position}
方向：${currentJob.category.join('、')}
岗位要求：${currentJob.requirements.join('；')}
核心技能：${currentJob.tags.join('、')}

【我的背景】
学历：${edu1}
技能：${skills}
经历：${exp}

【请帮我完成】
1. 优化我的简历，突出与该岗位匹配的关键经历和技能
2. 写一封200字以内的求职信，重点说明为什么适合这个岗位
3. 给出3个可能的面试问题及回答思路

【注意事项】
- 语气专业但不过分正式
- 突出数据驱动、量化成果
- 与${currentJob.company}的企业文化和业务方向结合
`;
  }

  document.getElementById('sidebar-body').innerHTML = `<pre>${content}</pre>`;
}

function copySidebar() {
  const text = document.getElementById('sidebar-body').innerText;
  navigator.clipboard.writeText(text).then(() => showToast('已复制到剪贴板 ✓'));
}

function downloadSidebar() {
  const text = document.getElementById('sidebar-body').innerText;
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${currentJob.company}_${currentJob.position}_申请材料.txt`;
  a.click();
}

// ====== APPLIED ======
function markApplied(id) {
  if (appliedJobs.some(a => a.id === id)) return;
  const job = allJobs.find(j => j.id === id);
  appliedJobs.push({
    id,
    company: job.company,
    position: job.position,
    logo: job.logo,
    deadline: job.deadline,
    applyUrl: job.applyUrl,
    status: 'applied',
    timeline: [{ time: new Date().toLocaleString('zh-CN'), text: '提交投递' }],
    notes: ''
  });
  saveApplied();
  updateAppliedBadge();

  // 更新卡片状态
  const btn = document.getElementById(`apply-btn-${id}`);
  if (btn) {
    btn.textContent = '✅ 已投递';
    btn.classList.add('applied');
    btn.onclick = null;
    document.getElementById(`card-${id}`)?.classList.add('is-applied');
  }
  showToast('✅ 已标记为已投递，在「已投递」页面追踪进度');
}

function saveApplied() {
  localStorage.setItem('applied_jobs', JSON.stringify(appliedJobs));
}

function updateAppliedBadge() {
  const count = appliedJobs.length;
  const badge = document.getElementById('applied-badge');
  if (count > 0) {
    badge.textContent = count;
    badge.style.display = 'inline';
  } else {
    badge.style.display = 'none';
  }
}

function renderApplied() {
  const container = document.getElementById('applied-list');
  const empty = document.getElementById('applied-empty');

  if (!appliedJobs.length) {
    empty.style.display = 'block';
    container.innerHTML = '';
    return;
  }
  empty.style.display = 'none';

  const statusMap = {
    'applied': '⏳ 已投递，等待中',
    'email': '📧 收到邮件回复',
    'interview': '📞 收到面试邀请',
    'offer': '🎉 已收到Offer',
    'rejected': '❌ 未通过',
    'withdrawn': '🚫 已撤回'
  };

  container.innerHTML = appliedJobs.map((a, idx) => `
    <div class="applied-card">
      <div class="applied-card-header">
        <div>
          <div class="applied-company">${a.logo} ${a.company}</div>
          <div class="applied-position">${a.position}</div>
          <div style="font-size:0.78rem;color:#999;margin-top:0.3rem">截止 ${a.deadline}</div>
        </div>
        <div style="text-align:right">
          <select class="status-select" onchange="updateStatus(${idx}, this.value)">
            ${Object.entries(statusMap).map(([k,v]) => `<option value="${k}" ${a.status===k?'selected':''}>${v}</option>`).join('')}
          </select>
          <div class="applied-remove" onclick="removeApplied(${idx})" style="margin-top:0.4rem">移除</div>
        </div>
      </div>
      <div class="timeline">
        ${a.timeline.slice().reverse().map(t => `
          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div><span class="timeline-time">${t.time}</span> ${t.text}</div>
          </div>
        `).join('')}
      </div>
      <textarea class="notes-input" rows="2" placeholder="添加备注（如：收到HR邮件，要求提供成绩单）" onchange="updateNotes(${idx}, this.value)">${a.notes}</textarea>
      <div style="margin-top:0.5rem">
        <a href="${a.applyUrl}" target="_blank" style="font-size:0.8rem;color:#4a6fa5">前往官网 →</a>
      </div>
    </div>
  `).join('');
}

function updateStatus(idx, status) {
  const statusText = {
    'applied': '标记为：等待中',
    'email': '标记为：收到邮件',
    'interview': '🎉 收到面试邀请！',
    'offer': '🎊 恭喜收到Offer！',
    'rejected': '标记为：未通过',
    'withdrawn': '标记为：已撤回'
  };
  appliedJobs[idx].status = status;
  appliedJobs[idx].timeline.push({ time: new Date().toLocaleString('zh-CN'), text: statusText[status] });
  saveApplied();
  renderApplied();
}

function updateNotes(idx, notes) {
  appliedJobs[idx].notes = notes;
  saveApplied();
}

function removeApplied(idx) {
  appliedJobs.splice(idx, 1);
  saveApplied();
  updateAppliedBadge();
  renderApplied();
}

// ====== PAGE NAV ======
function showPage(page) {
  document.getElementById('page-jobs').style.display = page === 'jobs' ? 'block' : 'none';
  document.getElementById('page-applied').style.display = page === 'applied' ? 'block' : 'none';
  document.getElementById('filters-bar').style.display = page === 'jobs' ? 'flex' : 'none';
  document.getElementById('tab-jobs').classList.toggle('active', page === 'jobs');
  document.getElementById('tab-applied').classList.toggle('active', page === 'applied');
  if (page === 'applied') renderApplied();
}

// ====== PROFILE ======
function openProfile() {
  const p = userProfile;
  document.getElementById('p-name').value = p.name || '';
  document.getElementById('p-edu1').value = p.edu1 || '';
  document.getElementById('p-edu2').value = p.edu2 || '';
  document.getElementById('p-exp').value = p.exp || '';
  document.getElementById('p-skills').value = p.skills || '';
  document.getElementById('p-resume').value = p.resume || '';
  document.getElementById('p-coverletter').value = p.coverletter || '';
  renderTags();
  document.getElementById('profile-overlay').style.display = 'block';
  document.getElementById('profile-modal').classList.add('active');
}

function closeProfile() {
  document.getElementById('profile-overlay').style.display = 'none';
  document.getElementById('profile-modal').classList.remove('active');
}

function saveProfile() {
  userProfile = {
    name: document.getElementById('p-name').value,
    edu1: document.getElementById('p-edu1').value,
    edu2: document.getElementById('p-edu2').value,
    exp: document.getElementById('p-exp').value,
    skills: document.getElementById('p-skills').value,
    resume: document.getElementById('p-resume').value,
    coverletter: document.getElementById('p-coverletter').value
  };
  localStorage.setItem('user_profile', JSON.stringify(userProfile));
  localStorage.setItem('user_tags', JSON.stringify(userTags));
  closeProfile();
  showToast('✅ 信息已保存');
}

function addTag(e) {
  if (e.key === 'Enter') {
    const val = e.target.value.trim();
    if (val && !userTags.includes(val)) {
      userTags.push(val);
      renderTags();
    }
    e.target.value = '';
  }
}

function removeTag(tag) {
  userTags = userTags.filter(t => t !== tag);
  renderTags();
}

function renderTags() {
  document.getElementById('tags-display').innerHTML = userTags.map(t =>
    `<div class="tag-item">${t} <span onclick="removeTag('${t}')">✕</span></div>`
  ).join('');
}

// ====== TOAST ======
function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

// ====== START ======
init();
