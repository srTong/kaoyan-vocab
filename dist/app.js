// 首页 JavaScript
let appData = null;
const DATA_VERSION = '20261027-quality-gate-18';
let nonHighFreqWords = [];
let selectedScopes = [];

function loadSavedScopes() {
    try {
        const saved = JSON.parse(localStorage.getItem('vocabScopes') || 'null');
        selectedScopes = Array.isArray(saved) ? saved : ['考研'];
    } catch (_) {
        selectedScopes = ['考研'];
    }
}

function saveScopes() {
    localStorage.setItem('vocabScopes', JSON.stringify(selectedScopes));
}

function wordMatchesScope(word) {
    return selectedScopes.length === 0 || (word.scopes || []).some(scope => selectedScopes.includes(scope));
}

function displayMeaning(word) {
    const meaning = (word.meaning || '').trim();
    const suspicious = !meaning || /(待校对|待补充|相关的|有关的)/.test(meaning) ||
        /(^|[；，\n])\s*(a|ad|adv|n|v|vt|vi|prep|conj)\./i.test(meaning) ||
        /[A-Za-z]{3,}/.test(meaning);
    return suspicious ? '释义待校对' : meaning;
}

function getFilteredRoots() {
    return appData.roots.map(root => ({
        ...root,
        words: root.words.filter(wordMatchesScope)
    })).filter(root => root.words.length > 0);
}

// 加载数据
async function loadData() {
    try {
        const response = await fetch(`data/data.json?v=${DATA_VERSION}`);
        appData = await response.json();
        loadSavedScopes();
        selectedScopes = selectedScopes.filter(scope => (appData.availableScopes || []).includes(scope));
        renderScopeFilters();
        renderRoots();
        updateStats();
        
        // 加载非高频词汇
        await loadNonHighFreqWords();
    } catch (error) {
        console.error('加载数据失败:', error);
        alert('加载数据失败，请刷新页面重试');
    }
}

// 加载非高频词汇
async function loadNonHighFreqWords() {
    try {
        const response = await fetch('data/non_high_freq.json');
        nonHighFreqWords = await response.json();
        renderNonHighFreqWords();
    } catch (error) {
        console.error('加载非高频词汇失败:', error);
    }
}

// 渲染非高频词汇
function renderNonHighFreqWords() {
    const container = document.getElementById('nonHighFreqList');
    
    container.innerHTML = nonHighFreqWords.map(word => {
        return `
            <div class="non-high-freq-card">
                <div class="word">${word.word}</div>
                <div class="meaning">${displayMeaning(word)}</div>
            </div>
        `;
    }).join('');
}

// 更新统计信息
function updateStats() {
    const roots = getFilteredRoots();
    const words = roots.flatMap(root => root.words);
    document.getElementById('rootCount').textContent = roots.length;
    document.getElementById('wordCount').textContent = words.length;
    document.getElementById('exampleCount').textContent = words.filter(word => word.example).length;
}

function renderScopeFilters() {
    const container = document.getElementById('scopeFilters');
    const scopes = appData.availableScopes || [];
    container.innerHTML = scopes.map(scope => {
        const count = appData.roots.reduce((sum, root) =>
            sum + root.words.filter(word => (word.scopes || []).includes(scope)).length, 0);
        const active = selectedScopes.includes(scope);
        return `<button type="button" class="scope-chip${active ? ' active' : ''}"
            aria-pressed="${active}" data-scope="${scope}">${scope}<span>${count}</span></button>`;
    }).join('');

    container.querySelectorAll('.scope-chip').forEach(button => {
        button.addEventListener('click', () => {
            const scope = button.dataset.scope;
            selectedScopes = selectedScopes.includes(scope)
                ? selectedScopes.filter(item => item !== scope)
                : [...selectedScopes, scope];
            saveScopes();
            renderScopeFilters();
            renderRoots();
            updateStats();
            updateAuxiliarySections();
        });
    });
    const allButton = document.getElementById('allScopesBtn');
    allButton.classList.toggle('active', selectedScopes.length === 0);
    allButton.setAttribute('aria-pressed', String(selectedScopes.length === 0));
}

function updateAuxiliarySections() {
    const section = document.querySelector('.non-high-freq-section');
    if (section) section.hidden = selectedScopes.length > 0;
}

// 渲染词根列表
function renderRoots() {
    const container = document.getElementById('rootsList');
    
    container.innerHTML = getFilteredRoots().map(root => {
        const wordCount = root.words.length;
        const exampleCount = root.words.filter(w => w.example).length;
        
        // 生成词源故事预览（取前80个字符）
        let storyPreview = '';
        if (root.story) {
            storyPreview = root.story.length > 80 
                ? root.story.substring(0, 80) + '...' 
                : root.story;
        }
        
        return `
            <div class="root-card" onclick="goToRoot('${encodeURIComponent(root.name)}')">
                <h3>${root.name}</h3>
                <p>${root.meaning || '核心词根'}</p>
                ${storyPreview ? `<div class="story-preview">${storyPreview}</div>` : ''}
                <div class="word-count">
                    ${wordCount} 个单词 · ${exampleCount} 个例句
                </div>
            </div>
        `;
    }).join('');
}

// 跳转到词根详情页
function goToRoot(rootName) {
    const scopeQuery = selectedScopes.length ? `&scopes=${encodeURIComponent(selectedScopes.join(','))}` : '';
    window.location.href = `root.html?root=${rootName}${scopeQuery}`;
}

// 开始练习
document.getElementById('practiceBtn').addEventListener('click', () => {
    const scopeQuery = selectedScopes.length ? `?scopes=${encodeURIComponent(selectedScopes.join(','))}` : '';
    window.location.href = `practice.html${scopeQuery}`;
});

document.getElementById('allScopesBtn').addEventListener('click', () => {
    selectedScopes = [];
    saveScopes();
    renderScopeFilters();
    renderRoots();
    updateStats();
    updateAuxiliarySections();
});

// 页面加载时初始化
window.addEventListener('DOMContentLoaded', () => {
    loadData().then(updateAuxiliarySections);
});
